
import pytest

from app.tools.tool_agent import (
    choose_tool,
    execute_tool_decision,
    parse_math_task,
)


@pytest.mark.parametrize(
    ("task", "expected"),
    [
        ("Calculate 50 multiplied by 3 and then add 20.", 170),
        ("Calculate 125 plus 275.", 400),
        ("What is 144 divided by 12?", 12),
        ("Calculate 20 multiplied by 5, then add 15.", 115),
    ],
)
def test_calculator_routing_and_result(task, expected):
    decision = choose_tool(task)

    assert decision["use_tool"] is True
    assert decision["tool_name"] == "calculator"

    result = execute_tool_decision(decision)

    assert result["used"] is True
    assert "error" not in result
    assert result.get("result") == expected


def test_division_is_parsed_without_llm():
    assert parse_math_task("What is 144 divided by 12?") == "144 / 12"


def test_unsupported_math_expression_is_rejected():
    with pytest.raises(ValueError, match="Could not safely parse"):
        choose_tool("Calculate 5 factorial")
