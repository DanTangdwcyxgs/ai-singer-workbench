import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Separate vocals with BS-RoFormer.")
    parser.add_argument("--gpt-root", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--vocal-dir", required=True)
    parser.add_argument("--instrumental-dir", required=True)
    args = parser.parse_args()

    gpt_root = Path(args.gpt_root).resolve()
    uvr_root = gpt_root / "tools" / "uvr5"
    weight = uvr_root / "uvr5_weights" / args.model_name
    input_path = Path(args.input).resolve()
    vocal_dir = Path(args.vocal_dir).resolve()
    instrumental_dir = Path(args.instrumental_dir).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not weight.is_file():
        raise FileNotFoundError(weight)

    vocal_dir.mkdir(parents=True, exist_ok=True)
    instrumental_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(gpt_root)
    os.environ["PATH"] = str(gpt_root / "runtime") + os.pathsep + os.environ.get("PATH", "")
    sys.path.insert(0, str(gpt_root))
    sys.path.insert(0, str(uvr_root))

    import torch
    from tools.uvr5.bsroformer import Roformer_Loader

    loader = Roformer_Loader(
        model_path=str(weight),
        config_path=str(weight.with_suffix(".yaml")),
        device="cuda" if torch.cuda.is_available() else "cpu",
        is_half=bool(torch.cuda.is_available()),
    )
    loader.config["inference"]["batch_size"] = 1
    loader._path_audio_(
        str(input_path), str(instrumental_dir), str(vocal_dir), "wav"
    )

    vocal = vocal_dir / f"{input_path.stem}_vocals.wav"
    instrumental = instrumental_dir / f"{input_path.stem}_other.wav"
    if not vocal.is_file() or not instrumental.is_file():
        raise RuntimeError("Separation finished without both expected output files.")
    print(json.dumps({"vocal": str(vocal), "instrumental": str(instrumental)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
