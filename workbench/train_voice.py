import argparse
import shutil
import sys
from pathlib import Path

from helpers import SUPPORTED_AUDIO, matching_index, validate_model_name
from runner import run_logged
from settings import load_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and export one RVC voice model.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    settings = load_settings(args.config)
    model_name = validate_model_name(args.model_name)
    dataset = Path(args.dataset).resolve()
    if not dataset.is_dir():
        raise NotADirectoryError(dataset)
    if not any(p.suffix.lower() in SUPPORTED_AUDIO for p in dataset.iterdir()):
        raise RuntimeError("No supported audio files were found in the dataset.")
    if not 1 <= args.epochs <= 1000:
        raise ValueError("Epochs must be between 1 and 1000.")
    if not 1 <= args.batch_size <= 32:
        raise ValueError("Batch size must be between 1 and 32.")

    log_dir = settings.applio_root / "logs" / model_name
    export_dir = settings.directory("models") / model_name
    if export_dir.exists() and any(export_dir.iterdir()):
        raise RuntimeError("This model name already exists. Use a new name to protect it.")

    py = str(settings.applio_python)
    core = str(settings.applio_core)
    device = settings.device
    cores = "8"
    stage_log = settings.directory("logs") / f"train-{model_name}.log"

    commands = [
        [
            py, core, "preprocess", "--model_name", model_name,
            "--dataset_path", str(dataset), "--sample_rate", "48000",
            "--cpu_cores", cores, "--cut_preprocess", "Automatic",
            "--process_effects", "False", "--noise_reduction", "False",
            "--chunk_len", "3.0", "--overlap_len", "0.3",
            "--normalization_mode", "none",
        ],
        [
            py, core, "extract", "--model_name", model_name,
            "--f0_method", "rmvpe", "--cpu_cores", cores, "--gpu", device,
            "--sample_rate", "48000", "--embedder_model", "contentvec",
            "--include_mutes", "2",
        ],
        [
            py, core, "train", "--model_name", model_name,
            "--vocoder", "HiFi-GAN", "--save_every_epoch", "25",
            "--save_only_latest", "True", "--save_every_weights", "False",
            "--total_epoch", str(args.epochs), "--sample_rate", "48000",
            "--batch_size", str(args.batch_size), "--gpu", device,
            "--pretrained", "True", "--overtraining_detector", "True",
            "--overtraining_threshold", "30", "--cleanup", "False",
            "--cache_data_in_gpu", "False", "--checkpointing", "False",
            "--index_algorithm", "Auto",
        ],
    ]
    transcript = []
    for command in commands:
        transcript.append(run_logged(command, settings.applio_root, stage_log))
    stage_log.write_text("\n\n".join(transcript), encoding="utf-8")

    weights = sorted(
        [p for p in log_dir.glob("*.pth") if not p.name.startswith(("G_", "D_"))],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not weights:
        raise RuntimeError("Training finished without an exported .pth model.")
    index = matching_index(weights[0])
    export_dir.mkdir(parents=True, exist_ok=True)
    model_target = export_dir / f"{model_name}.pth"
    index_target = export_dir / f"{model_name}.index"
    shutil.copy2(weights[0], model_target)
    shutil.copy2(index, index_target)
    print(f"MODEL={model_target}")
    print(f"INDEX={index_target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
