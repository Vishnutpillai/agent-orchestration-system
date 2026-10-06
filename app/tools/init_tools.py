from app.tools.registry import tool_registry
from app.tools.calculator import calculator
from app.tools.file_reader import read_file
from app.tools.file_writer import write_file
from app.tools.code_executor import execute_python


def initialize_tools():

    tool_registry.register(
        name="calculator",
        description=(
            "Perform basic mathematical calculations "
            "using a mathematical expression."
        ),
        function=calculator,
    )

    tool_registry.register(
        name="file_read",
        description=(
            "Read the contents of a UTF-8 text file "
            "inside the project directory."
        ),
        function=read_file,
    )

    tool_registry.register(
        name="file_write",
        description=(
            "Write UTF-8 text content to a file "
            "inside the project directory."
        ),
        function=write_file,
    )

    tool_registry.register(
        name="code_execution",
        description=(
            "Execute a Python code snippet in a "
            "temporary restricted environment."
        ),
        function=execute_python,
    )

    return tool_registry