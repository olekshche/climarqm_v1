from __future__ import annotations

from pathlib import Path


def _sanitize_protocol_name(protocol_name: str) -> str:
    """
    Convert a user-provided protocol name into a safe filename stem.
    """
    if protocol_name is None:
        protocol_name = ""

    safe_name = protocol_name.strip()

    if not safe_name:
        safe_name = "protocol"

    allowed_chars = []
    for char in safe_name:
        if char.isalnum() or char in ("_", "-", " "):
            allowed_chars.append(char)

    safe_name = "".join(allowed_chars).strip().replace(" ", "_")

    if not safe_name:
        safe_name = "protocol"

    return safe_name


def save_protocol_text(protocol_name: str, protocol_text: str, protocols_dir: Path) -> Path:
    """
    Save protocol text into the protocols directory as a .txt file.
    """
    if protocol_text is None or not str(protocol_text).strip():
        raise ValueError("Protocol text is empty.")

    protocols_dir = Path(protocols_dir)
    protocols_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_protocol_name(protocol_name)
    output_path = protocols_dir / f"{safe_name}.txt"

    output_path.write_text(protocol_text, encoding="utf-8")

    return output_path


def list_protocol_files(protocols_dir: Path) -> list[Path]:
    protocols_dir = Path(protocols_dir)
    protocols_dir.mkdir(parents=True, exist_ok=True)
    return sorted(protocols_dir.glob("*.txt"))


def list_protocol_names(protocols_dir: Path) -> list[str]:
    return [path.name for path in list_protocol_files(protocols_dir)]


def load_protocol_text(protocol_filename: str, protocols_dir: Path) -> str:
    if protocol_filename is None or not str(protocol_filename).strip():
        raise ValueError("Protocol filename is empty.")

    protocol_path = Path(protocols_dir) / protocol_filename

    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol file '{protocol_filename}' was not found.")

    return protocol_path.read_text(encoding="utf-8")