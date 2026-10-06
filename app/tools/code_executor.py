import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def execute_python(code: str, timeout: int = 10) -> dict:
    """
    Execute a Python code snippet in a temporary file.

    The process is isolated from the project's files as much as
    possible and has a short execution timeout.
    """

    if not code or not code.strip():
        raise ValueError(
            "Python code cannot be empty."
        )

    if len(code) > 10000:
        raise ValueError(
            "Python code is too large."
        )

    # Basic protection against direct OS/process manipulation.
    blocked_patterns = [
        "os.system",
        "subprocess.",
        "shutil.rmtree",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "pathlib.Path(",
        "open(",
    ]

    code_lower = code.lower()

    for pattern in blocked_patterns:
        if pattern.lower() in code_lower:
            raise ValueError(
                f"Blocked operation detected: {pattern}"
            )

    timeout = max(1, min(timeout, 10))

    with tempfile.TemporaryDirectory(
        dir=PROJECT_ROOT
    ) as temp_dir:

        script_path = Path(temp_dir) / "script.py"

        script_path.write_text(
            code,
            encoding="utf-8",
        )

        try:

            process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }

        except subprocess.TimeoutExpired as exc:

            return {
                "success": False,
                "return_code": None,
                "stdout": exc.stdout or "",
                "stderr": (
                    "Execution timed out."
                ),
            }