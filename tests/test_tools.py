from app.tools import tool_registry


def test_calculator():

    result = tool_registry.execute(
        "calculator",
        expression="25 * 4",
    )

    assert result == 100


def test_calculator_addition():

    result = tool_registry.execute(
        "calculator",
        expression="100 + 50",
    )

    assert result == 150


def test_tool_exists():

    tool = tool_registry.get("calculator")

    assert tool is not None


def test_file_read():

    content = tool_registry.execute(
        "file_read",
        path="app/data/sample.txt",
    )

    assert "Agent Orchestration System" in content


def test_file_read_tool_exists():

    tool = tool_registry.get("file_read")

    assert tool is not None


def test_file_write(tmp_path):

    filename = (
        f"app/data/test_output_{tmp_path.name}.txt"
    )

    content = "Tool write test."

    result = tool_registry.execute(
        "file_write",
        path=filename,
        content=content,
    )

    assert "File written successfully" in result


def test_code_execution():

    result = tool_registry.execute(
        "code_execution",
        code="print(10 + 20)",
    )

    assert result["success"] is True
    assert "30" in result["stdout"]


def test_code_execution_error():

    result = tool_registry.execute(
        "code_execution",
        code="print(10 / 0)",
    )

    assert result["success"] is False


def test_code_execution_timeout():

    result = tool_registry.execute(
        "code_execution",
        code="while True: pass",
        timeout=1,
    )

    assert result["success"] is False
    assert "timed out" in result["stderr"].lower()
def test_tool_registry_contains_all_tools():

    tools = tool_registry.list_tools()

    names = {
        tool["name"]
        for tool in tools
    }

    assert "calculator" in names
    assert "file_read" in names
    assert "file_write" in names
    assert "code_execution" in names