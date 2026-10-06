from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_file(path: str) -> str:
    """
    Read a text file from inside the project directory.
    """

    requested_path = Path(path)

    if requested_path.is_absolute():
        full_path = requested_path.resolve()
    else:
        full_path = (PROJECT_ROOT / requested_path).resolve()

    # Security: prevent reading outside the project directory
    try:
        full_path.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            "Access denied: file is outside the project directory."
        ) from exc

    if not full_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not full_path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    try:
        return full_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError as exc:
        raise ValueError(
            "File is not a UTF-8 text file."
        ) from exc