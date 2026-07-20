import json
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"


def _find_root(candidate: Path, marker: str) -> Path:
    candidate = candidate.expanduser().resolve()
    if (candidate / marker).exists():
        return candidate
    matches = list(candidate.glob(f"**/{marker}")) if candidate.exists() else []
    if not matches:
        raise FileNotFoundError(f"Cannot find {marker} under {candidate}")
    return matches[0].parent


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_root: Path
    applio_root: Path
    gpt_sovits_root: Path | None
    server_host: str
    server_port: int
    separator_model: str
    device: str

    @property
    def applio_python(self) -> Path:
        return self.applio_root / "env" / "python.exe"

    @property
    def applio_core(self) -> Path:
        return self.applio_root / "core.py"

    @property
    def ffmpeg(self) -> Path:
        candidates = [
            self.applio_root / "ffmpeg.exe",
            self.applio_root / "env" / "Library" / "bin" / "ffmpeg.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError("FFmpeg was not found inside Applio.")

    @property
    def gpt_python(self) -> Path:
        if not self.gpt_sovits_root:
            raise FileNotFoundError("GPT-SoVITS is not configured.")
        return self.gpt_sovits_root / "runtime" / "python.exe"

    def directory(self, name: str) -> Path:
        path = self.data_root / name
        path.mkdir(parents=True, exist_ok=True)
        return path


def load_settings(config_path: str | Path | None = None) -> Settings:
    path = Path(
        config_path
        or os.environ.get("AI_SINGER_CONFIG", "")
        or PROJECT_ROOT / "config.json"
    ).resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {path}. Run scripts/configure-windows.ps1 first."
        )
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    applio = _find_root(Path(raw["applio_root"]), "core.py")
    gpt_value = str(raw.get("gpt_sovits_root", "")).strip()
    gpt = _find_root(Path(gpt_value), "tools/uvr5") if gpt_value else None
    settings = Settings(
        project_root=PROJECT_ROOT,
        data_root=DATA_ROOT,
        applio_root=applio,
        gpt_sovits_root=gpt,
        server_host=str(raw.get("server_host", "127.0.0.1")),
        server_port=int(raw.get("server_port", 9875)),
        separator_model=str(
            raw.get("separator_model", "model_bs_roformer_ep_317_sdr_12.9755.ckpt")
        ),
        device=str(raw.get("device", "0")),
    )
    for name in ("recordings", "songs", "separated", "models", "outputs", "logs"):
        settings.directory(name)
    return settings
