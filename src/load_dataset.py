import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "fastStorage"
SAMPLE_FILE = DATA_DIR / "1.csv"


def load_vm_trace(file_path: Path | str = SAMPLE_FILE) -> pd.DataFrame:
    """Load one Bitbrains GWA-T-12 VM trace CSV (semicolon-tab separated)."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"VM trace not found: {path}")
    return pd.read_csv(path, sep=";\t", engine="python")


def list_vm_trace_files(data_dir: Path | None = None) -> list[Path]:
    """Return sorted list of VM trace CSV paths (numeric order by filename stem)."""
    directory = data_dir or DATA_DIR
    if not directory.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {directory}")
    files = list(directory.glob("*.csv"))
    return sorted(files, key=lambda p: int(p.stem))


def vm_id_from_path(file_path: Path | str) -> int:
    """VM identifier from trace filename (e.g. 1.csv -> 1). Used in PHASE 2+."""
    return int(Path(file_path).stem)


if __name__ == "__main__":
    df = load_vm_trace()

    print(df.head())
    print()
    print(df.info())
    print()
    print(df.columns.tolist())
