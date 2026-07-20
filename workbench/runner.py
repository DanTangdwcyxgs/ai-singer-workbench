import os
import subprocess
from pathlib import Path


def run_logged(command: list[str], cwd: Path, log_path: Path) -> str:
    env = os.environ.copy()
    env["PATH"] = str(cwd) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    if result.returncode:
        tail = "\n".join(output.strip().splitlines()[-16:])
        raise RuntimeError(tail or f"Process exited with code {result.returncode}")
    return output
