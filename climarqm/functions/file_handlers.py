from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from climarqm.config.paths import TEMP_DIR


def summarize_uploaded_files(filenames, values) -> str:
    """
    Create a small markdown summary for uploaded files.

    Parameters
    ----------
    filenames : str | list[str] | None
        Uploaded file name or list of file names from Panel FileInput.
    values : bytes | list[bytes] | None
        Uploaded file content or list of file contents from Panel FileInput.

    Returns
    -------
    str
        Markdown summary.
    """
    if filenames is None:
        return "No files uploaded yet."

    if isinstance(filenames, str):
        filenames_list = [filenames]
    else:
        filenames_list = list(filenames)

    if values is None:
        values_list = [None] * len(filenames_list)
    elif isinstance(values, (bytes, bytearray)):
        values_list = [values]
    else:
        values_list = list(values)

    lines = ["### Uploaded files", ""]

    for i, name in enumerate(filenames_list):
        size_info = ""
        if i < len(values_list) and values_list[i] is not None:
            try:
                file_size = len(values_list[i])
                size_info = f" ({file_size} bytes)"
            except Exception:
                size_info = ""

        lines.append(f"- `{name}`{size_info}")

    if len(filenames_list) == 0:
        return "No files uploaded yet."

    return "\n".join(lines)


def _normalize_uploaded_lists(filenames, values) -> tuple[list[str], list[bytes | bytearray | None]]:
    if filenames is None:
        return [], []

    if isinstance(filenames, str):
        filenames_list = [filenames]
    else:
        filenames_list = list(filenames)

    if values is None:
        values_list = [None] * len(filenames_list)
    elif isinstance(values, (bytes, bytearray)):
        values_list = [values]
    else:
        values_list = list(values)

    return filenames_list, values_list


def _sanitize_uploaded_filename(filename: str) -> str:
    raw_name = Path(filename or "uploaded_file").name.strip()
    if not raw_name:
        raw_name = "uploaded_file"

    safe_chars = []
    for char in raw_name:
        if char.isalnum() or char in (".", "_", "-"):
            safe_chars.append(char)
        else:
            safe_chars.append("_")

    safe_name = "".join(safe_chars).strip("._")
    if not safe_name:
        safe_name = "uploaded_file"

    return safe_name


def get_upload_session_dir(session_name: str = "current_upload") -> Path:
    session_dir = Path(TEMP_DIR) / session_name
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def clear_upload_session_dir(session_name: str = "current_upload") -> Path:
    session_dir = Path(TEMP_DIR) / session_name
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def save_uploaded_files(
    filenames,
    values,
    session_name: str = "current_upload",
) -> list[str]:
    """
    Save uploaded files from Panel FileInput into a temporary session folder.

    Returns
    -------
    list[str]
        Full file paths of saved uploaded files.
    """
    filenames_list, values_list = _normalize_uploaded_lists(filenames, values)

    session_dir = clear_upload_session_dir(session_name=session_name)

    saved_paths: list[str] = []

    for i, filename in enumerate(filenames_list):
        safe_name = _sanitize_uploaded_filename(filename)

        if i >= len(values_list) or values_list[i] is None:
            continue

        output_path = session_dir / safe_name
        output_path.write_bytes(bytes(values_list[i]))
        saved_paths.append(str(output_path))

    return saved_paths


def format_saved_paths_markdown(saved_paths: Iterable[str]) -> str:
    saved_paths = list(saved_paths)

    if not saved_paths:
        return "No uploaded files saved yet."

    lines = ["### Saved upload paths", ""]
    for path in saved_paths:
        lines.append(f"- `{path}`")

    return "\n".join(lines)