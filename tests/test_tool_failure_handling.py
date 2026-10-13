from app.agents import tool_loop_agent, approved_tool_agent


def test_tool_loop_records_failed_tool(monkeypatch):
    monkeypatch.setattr(
        tool_loop_agent,
        "choose_tool",
        lambda task, context=None: {
            "use_tool": True,
            "tool_name": "calculator",
            "arguments": {"expression": "1 / 0"},
            "reason": "Test failure",
        },
    )

    monkeypatch.setattr(
        tool_loop_agent,
        "execute_tool_decision",
        lambda decision: {
            "used": True,
            "tool_name": "calculator",
            "result": None,
            "error": "Division by zero",
        },
    )

    result = tool_loop_agent.tool_loop_node(
        {
            "task": "Calculate 1 divided by 0",
            "results": [],
            "tool_calls": 0,
        }
    )

    assert result["results"][-1]["status"] == "failed"
    assert "Division by zero" in result["results"][-1]["output"]
    assert result["tool_result"]["error"] == "Division by zero"


def test_approved_tool_records_failed_execution(monkeypatch):
    monkeypatch.setattr(
        approved_tool_agent,
        "execute_tool_decision",
        lambda decision: {
            "used": True,
            "tool_name": "file_write",
            "result": None,
            "error": "Permission denied",
        },
    )

    result = approved_tool_agent.execute_approved_tool_node(
        {
            "task": "Write a test file",
            "human_decision": "approved",
            "tool_decision": {
                "use_tool": True,
                "tool_name": "file_write",
                "arguments": {},
            },
            "results": [],
            "tool_calls": 0,
        }
    )

    assert result["results"][-1]["status"] == "failed"
    assert "Permission denied" in result["results"][-1]["output"]


def test_unapproved_tool_is_recorded_as_failed():
    result = approved_tool_agent.execute_approved_tool_node(
        {
            "task": "Write a test file",
            "human_decision": "rejected",
            "tool_decision": {
                "use_tool": True,
                "tool_name": "file_write",
                "arguments": {},
            },
            "results": [],
        }
    )

    assert result["results"][-1]["status"] == "failed"
    assert "not approved" in result["results"][-1]["output"].lower()
    assert result["tool_result"]["used"] is False