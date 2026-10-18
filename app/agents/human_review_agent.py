
from langgraph.types import interrupt


def human_review_node(state):
    """Pause the graph until a person approves or rejects the action."""

    approval_request = {
        "task": state.get("task", ""),
        "reason": state.get(
            "escalation_reason",
            "Human approval required.",
        ),
        "approval_level": state.get(
            "approval_level",
            "approve_action",
        ),
        "tool": state.get("selected_tool"),
    }

    # The graph pauses here. It resumes when Command(resume=...)
    # supplies a decision for this interrupt.
    decision = interrupt(approval_request)

    if not isinstance(decision, dict):
        decision = {}

    action = str(decision.get("decision", "")).strip().lower()
    feedback = str(decision.get("feedback", "")).strip()

    if action == "approve":
        return {
            "human_decision": "approved",
            "human_feedback": feedback or "Approved by human reviewer.",
            "requires_human": False,
        }

    # Reject by default if the supplied decision is invalid.
    return {
        "human_decision": "rejected",
        "human_feedback": feedback or "Rejected by human reviewer.",
        "requires_human": False,
    }
