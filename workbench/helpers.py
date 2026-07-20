import re
from pathlib import Path


SUPPORTED_AUDIO = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


def safe_name(value: str, fallback: str = "audio", limit: int = 48) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", (value or "").strip()).strip("_")
    return (cleaned[:limit] or fallback)


def validate_model_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,40}", value or ""):
        raise ValueError(
            "Model name must contain 2-40 English letters, numbers, underscores, or hyphens."
        )
    return value


def model_pairs(models_root: Path) -> list[tuple[str, str]]:
    pairs = []
    for model in sorted(models_root.glob("*/*.pth")):
        indexes = sorted(model.parent.glob("*.index"))
        if indexes:
            pairs.append((model.parent.name, str(model)))
    return pairs


def matching_index(model_path: Path) -> Path:
    indexes = sorted(model_path.parent.glob("*.index"))
    if not indexes:
        raise FileNotFoundError(f"No .index file found beside {model_path.name}")
    return indexes[-1]
