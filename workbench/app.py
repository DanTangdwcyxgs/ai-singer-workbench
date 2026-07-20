import argparse
import shutil
import time
from pathlib import Path

import gradio as gr

from helpers import SUPPORTED_AUDIO, matching_index, model_pairs, safe_name
from runner import run_logged
from settings import Settings, load_settings


def _copy_audio(source: str | Path, destination: Path) -> Path:
    source = Path(source)
    if source.suffix.lower() not in SUPPORTED_AUDIO:
        raise ValueError(f"Unsupported audio format: {source.suffix}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _convert_vocal(
    settings: Settings,
    vocal: Path,
    model: Path,
    output: Path,
    pitch: int,
    autotune: bool,
    stamp: str,
) -> None:
    index = matching_index(model)
    command = [
        str(settings.applio_python), str(settings.applio_core), "infer",
        "--pitch", str(int(pitch)), "--index_rate", "0.3",
        "--volume_envelope", "1.0", "--protect", "0.33",
        "--f0_method", "rmvpe", "--input_path", str(vocal),
        "--output_path", str(output), "--pth_path", str(model),
        "--index_path", str(index), "--split_audio", "True",
        "--f0_autotune", str(bool(autotune)),
        "--f0_autotune_strength", "0.2", "--clean_audio", "False",
        "--export_format", "WAV", "--embedder_model", "contentvec",
    ]
    run_logged(
        command,
        settings.applio_root,
        settings.directory("logs") / f"convert-{stamp}.log",
    )


def _mix_and_export(
    settings: Settings,
    converted: Path,
    instrumental: Path,
    base_name: str,
    vocal_gain: float,
    stamp: str,
) -> tuple[Path, Path]:
    output_wav = settings.directory("outputs") / f"{stamp}-{base_name}-AI.wav"
    output_mp3 = settings.directory("outputs") / f"{stamp}-{base_name}-AI.mp3"
    graph = (
        f"[0:a]volume={float(vocal_gain):.2f}[v];"
        "[1:a]volume=1.0[i];"
        "[v][i]amix=inputs=2:duration=longest:dropout_transition=0,"
        "alimiter=limit=0.95[out]"
    )
    run_logged(
        [
            str(settings.ffmpeg), "-y", "-i", str(converted),
            "-i", str(instrumental), "-filter_complex", graph,
            "-map", "[out]", "-ar", "44100", "-ac", "2",
            "-c:a", "pcm_s16le", str(output_wav),
        ],
        settings.applio_root,
        settings.directory("logs") / f"mix-{stamp}.log",
    )
    run_logged(
        [
            str(settings.ffmpeg), "-y", "-i", str(output_wav),
            "-c:a", "libmp3lame", "-b:a", "320k", str(output_mp3),
        ],
        settings.applio_root,
        settings.directory("logs") / f"export-{stamp}.log",
    )
    return output_wav, output_mp3


def build_app(settings: Settings, config_path: Path) -> gr.Blocks:
    models_root = settings.directory("models")

    def refresh_models():
        choices = model_pairs(models_root)
        value = choices[0][1] if choices else None
        return gr.update(choices=choices, value=value)

    def train_model(files, model_name, epochs, batch_size):
        if not files:
            return "请先上传个人录音。"
        name = safe_name(model_name, "my_voice", 40)
        dataset = settings.directory("recordings") / name
        dataset.mkdir(parents=True, exist_ok=True)
        copied = 0
        for item in files:
            source = Path(item)
            if source.suffix.lower() not in SUPPORTED_AUDIO:
                continue
            copied += 1
            _copy_audio(source, dataset / f"{copied:03d}_{source.name}")
        if not copied:
            return "没有找到支持的音频文件。"
        try:
            run_logged(
                [
                    str(settings.applio_python),
                    str(settings.project_root / "workbench" / "train_voice.py"),
                    "--config", str(config_path), "--dataset", str(dataset),
                    "--model-name", name, "--epochs", str(int(epochs)),
                    "--batch-size", str(int(batch_size)),
                ],
                settings.project_root / "workbench",
                settings.directory("logs") / f"training-wrapper-{name}.log",
            )
            return f"训练完成。模型保存在：{models_root / name}"
        except Exception as exc:
            return f"训练失败：{exc}"

    def make_cover(song_file, model_value, pitch, vocal_gain, autotune):
        if not song_file or not model_value:
            return "请上传歌曲并选择声音模型。", None, None
        if not settings.gpt_sovits_root:
            return "未配置 GPT-SoVITS，不能自动分离歌曲。", None, None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        source = Path(song_file)
        name = safe_name(source.stem, "song")
        saved = _copy_audio(
            source, settings.directory("songs") / f"{stamp}-{name}{source.suffix.lower()}"
        )
        work = settings.directory("separated") / f"{stamp}-{name}"
        vocal_dir = work / "vocal"
        instrumental_dir = work / "instrumental"
        vocal_dir.mkdir(parents=True, exist_ok=True)
        instrumental_dir.mkdir(parents=True, exist_ok=True)
        try:
            run_logged(
                [
                    str(settings.gpt_python),
                    str(settings.project_root / "workbench" / "separate_vocals.py"),
                    "--gpt-root", str(settings.gpt_sovits_root),
                    "--model-name", settings.separator_model,
                    "--input", str(saved), "--vocal-dir", str(vocal_dir),
                    "--instrumental-dir", str(instrumental_dir),
                ],
                settings.gpt_sovits_root,
                settings.directory("logs") / f"separate-{stamp}.log",
            )
            vocal = vocal_dir / f"{saved.stem}_vocals.wav"
            instrumental = instrumental_dir / f"{saved.stem}_other.wav"
            converted = work / f"{name}-converted.wav"
            _convert_vocal(
                settings, vocal, Path(model_value), converted,
                int(pitch), bool(autotune), stamp,
            )
            wav, mp3 = _mix_and_export(
                settings, converted, instrumental, name, float(vocal_gain), stamp
            )
            return f"制作完成：{mp3}", str(wav), str(mp3)
        except Exception as exc:
            return f"制作失败：{exc}", None, None

    def make_original(vocal_file, instrumental_file, model_value, pitch, vocal_gain, autotune):
        if not vocal_file or not instrumental_file or not model_value:
            return "请上传引导人声、伴奏并选择声音模型。", None, None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        vocal_source = Path(vocal_file)
        instrumental_source = Path(instrumental_file)
        name = safe_name(vocal_source.stem, "original")
        work = settings.directory("separated") / f"{stamp}-{name}-original"
        vocal = _copy_audio(vocal_source, work / f"guide{vocal_source.suffix.lower()}")
        instrumental = _copy_audio(
            instrumental_source,
            work / f"instrumental{instrumental_source.suffix.lower()}",
        )
        converted = work / f"{name}-converted.wav"
        try:
            _convert_vocal(
                settings, vocal, Path(model_value), converted,
                int(pitch), bool(autotune), stamp,
            )
            wav, mp3 = _mix_and_export(
                settings, converted, instrumental, name, float(vocal_gain), stamp
            )
            return f"原创歌曲制作完成：{mp3}", str(wav), str(mp3)
        except Exception as exc:
            return f"制作失败：{exc}", None, None

    def system_status():
        checks = [
            ("Applio Python", settings.applio_python.is_file()),
            ("Applio core.py", settings.applio_core.is_file()),
            ("FFmpeg", settings.ffmpeg.is_file()),
            ("GPT-SoVITS", bool(settings.gpt_sovits_root)),
        ]
        if settings.gpt_sovits_root:
            weight = (
                settings.gpt_sovits_root / "tools" / "uvr5" /
                "uvr5_weights" / settings.separator_model
            )
            checks.append(("BS-RoFormer", weight.is_file()))
        return "\n".join(f"{'通过' if ok else '未配置'}：{label}" for label, ok in checks)

    initial_models = model_pairs(models_root)
    initial_value = initial_models[0][1] if initial_models else None
    with gr.Blocks(title="AI 歌手工作台", analytics_enabled=False) as app:
        gr.Markdown("# AI 歌手工作台\n训练自己的声音，制作 AI 翻唱和原创 AI 歌曲。")
        with gr.Tab("训练我的声音"):
            with gr.Row():
                recordings = gr.File(
                    label="个人干声录音", file_count="multiple", type="filepath"
                )
                with gr.Column():
                    model_name = gr.Textbox(label="模型名称（英文）", value="my_voice")
                    epochs = gr.Slider(50, 500, value=300, step=25, label="训练轮数")
                    batch_size = gr.Slider(1, 8, value=4, step=1, label="批量大小")
                    train_button = gr.Button("开始完整训练", variant="primary")
            train_status = gr.Textbox(label="训练状态", interactive=False, lines=6)
            train_button.click(
                train_model,
                [recordings, model_name, epochs, batch_size],
                train_status,
            )

        with gr.Tab("AI 翻唱"):
            with gr.Row():
                song = gr.File(label="完整歌曲", type="filepath")
                with gr.Column():
                    cover_model = gr.Dropdown(
                        label="我的声音模型", choices=initial_models, value=initial_value
                    )
                    cover_refresh = gr.Button("刷新模型列表")
                    cover_pitch = gr.Slider(-12, 12, value=0, step=1, label="升降调（半音）")
                    cover_gain = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="人声音量")
                    cover_tune = gr.Checkbox(label="轻度音准修正", value=False)
                    cover_button = gr.Button("开始制作翻唱", variant="primary")
            cover_status = gr.Textbox(label="制作状态", interactive=False, lines=5)
            cover_preview = gr.Audio(label="AI 翻唱试听", type="filepath")
            cover_download = gr.File(label="下载 MP3")
            cover_refresh.click(refresh_models, outputs=cover_model)
            cover_button.click(
                make_cover,
                [song, cover_model, cover_pitch, cover_gain, cover_tune],
                [cover_status, cover_preview, cover_download],
            )

        with gr.Tab("原创歌曲"):
            gr.Markdown("上传 OpenUtau、DiffSinger 或其他工具生成的原创干声引导轨，以及对应原创伴奏。")
            with gr.Row():
                guide_vocal = gr.File(label="原创引导人声", type="filepath")
                original_instrumental = gr.File(label="原创伴奏", type="filepath")
                with gr.Column():
                    original_model = gr.Dropdown(
                        label="我的声音模型", choices=initial_models, value=initial_value
                    )
                    original_refresh = gr.Button("刷新模型列表")
                    original_pitch = gr.Slider(-12, 12, value=0, step=1, label="升降调（半音）")
                    original_gain = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="人声音量")
                    original_tune = gr.Checkbox(label="轻度音准修正", value=False)
                    original_button = gr.Button("制作原创歌曲", variant="primary")
            original_status = gr.Textbox(label="制作状态", interactive=False, lines=5)
            original_preview = gr.Audio(label="原创歌曲试听", type="filepath")
            original_download = gr.File(label="下载 MP3")
            original_refresh.click(refresh_models, outputs=original_model)
            original_button.click(
                make_original,
                [
                    guide_vocal, original_instrumental, original_model,
                    original_pitch, original_gain, original_tune,
                ],
                [original_status, original_preview, original_download],
            )

        with gr.Tab("系统检查"):
            status = gr.Textbox(value=system_status(), label="组件状态", lines=8)
            refresh_status = gr.Button("重新检查")
            refresh_status.click(system_status, outputs=status)
    return app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    settings = load_settings(config_path)
    app = build_app(settings, config_path)
    app.queue(default_concurrency_limit=1).launch(
        server_name=settings.server_host,
        server_port=settings.server_port,
        inbrowser=not args.no_browser,
        show_error=True,
        allowed_paths=[str(settings.data_root)],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
