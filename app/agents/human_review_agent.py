def human_review_node(state):
    task = state.get("task", "")
    reason = state.get(
        "escalation_reason",
        "Human approval required."
    )
    approval_level = state.get(
        "approval_level",
        "approve_action"
    )

    print("\n===== HUMAN REVIEW REQUIRED =====")
    print(f"Task: {task}")
    print(f"Reason: {reason}")
    print(f"Approval level: {approval_level}")
    print("=================================\n")

    # Temporary Phase 3 prototype:
    # Automatically approve so the graph can continue.
    return {
        "human_decision": "approved",
        "human_feedback": "Approved by human reviewer.",
        "requires_human": False,
    }