"""Run preprocess -> train -> evaluate -> export predictions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(SRC / script), *args]
    print("\n>>>", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    run("preprocess.py")
    run("train_model.py")
    run("evaluate_model.py")
    run("predict_workload.py")
    print("\nML pipeline complete.")


if __name__ == "__main__":
    main()
