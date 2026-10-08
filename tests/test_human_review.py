from app.agents.human_review_agent import human_review_node
from app.agents.tool_loop_agent import HUMAN_APPROVAL_TOOLS


def test_risky_tools_require_human_approval():
    assert "file_write" in HUMAN_APPROVAL_TOOLS
    assert "code_execution" in HUMAN_APPROVAL_TOOLS


def test_safe_tool_does_not_require_human_approval():
    assert "calculator" not in HUMAN_APPROVAL_TOOLS
    assert "file_read" not in HUMAN_APPROVAL_TOOLS


def test_human_review_approves_request():

    state = {
        "task": "Create a Python file",
        "requires_human": True,
        "escalation_reason": (
            "Human approval required before executing 'file_write'."
        ),
        "approval_level": "approve_action",
    }

    result = human_review_node(state)

    assert result["human_decision"] == "approved"
    assert result["requires_human"] is False
    assert "Approved" in result["human_feedback"]