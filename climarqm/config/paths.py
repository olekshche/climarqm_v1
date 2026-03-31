from pathlib import Path

# Root package directory: .../climarqm
PACKAGE_DIR = Path(__file__).resolve().parents[1]

# Project root directory: one level above package directory
PROJECT_ROOT = PACKAGE_DIR.parent

# Application data directories
PROTOCOLS_DIR = PACKAGE_DIR / "protocols"
DATA_DIR = PACKAGE_DIR / "data"
OUTPUTS_DIR = PACKAGE_DIR / "outputs"
TEMP_DIR = PACKAGE_DIR / "temp"


def ensure_project_dirs() -> None:
    """
    Create the main project directories if they do not exist.
    """
    for directory in (PROTOCOLS_DIR, DATA_DIR, OUTPUTS_DIR, TEMP_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# Ensure directories exist at import time
ensure_project_dirs()