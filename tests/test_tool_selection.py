from app.tools.tool_agent import (
    choose_tool,
    evaluate_math_expression,
    parse_math_task,
)


def test_calculator_selection_does_not_need_llm():
    decision = choose_tool("Calculate 12 multiplied by 3")

    assert decision["use_tool"] is True
    assert decision["tool_name"] == "calculator"
    assert decision["arguments"]["expression"] == "12 * 3"


def test_calculator_evaluates_expression_safely():
    assert evaluate_math_expression("12 * 3") == 36


def test_unsupported_math_expression_is_rejected():
    try:
        evaluate_math_expression("__import__('os').system('dir')")
    except (ValueError, TypeError, SyntaxError):
        pass
    else:
        raise AssertionError("Unsafe expression should be rejected")


def test_file_write_is_selected_for_approval():
    decision = choose_tool("Create a file called report.txt")

    assert decision["use_tool"] is True
    assert decision["tool_name"] == "file_write"


def test_unrelated_task_does_not_select_a_tool():
    decision = choose_tool("Explain how machine learning works")

    assert decision["use_tool"] is False