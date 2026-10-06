from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_file(path: str, content: str) -> str:
    """
    Write text content to a file inside the project directory.
    """

    requested_path = Path(path)

    if requested_path.is_absolute():
        full_path = requested_path.resolve()
    else:
        full_path = (PROJECT_ROOT / requested_path).resolve()

    # Security: prevent writing outside the project directory
    try:
        full_path.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            "Access denied: file is outside the project directory."
        ) from exc

    # Prevent accidental modification of sensitive files
    protected_names = {
        ".env",
        ".gitignore",
    }

    if full_path.name in protected_names:
        raise ValueError(
            f"Writing to '{full_path.name}' is not allowed."
        )

    full_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        full_path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError as exc:
        raise ValueError(
            f"Could not write file: {path}"
        ) from exc

    return (
        f"File written successfully: "
        f"{full_path.relative_to(PROJECT_ROOT)}"
    )