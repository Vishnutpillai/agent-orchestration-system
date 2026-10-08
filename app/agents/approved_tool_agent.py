from app.tools.tool_agent import execute_tool_decision


def execute_approved_tool_node(state):
    """
    Execute a tool only after human approval.
    """

    decision = state.get("tool_decision", {})

    if state.get("human_decision") != "approved":
        return {
            "tool_result": {
                "used": False,
                "tool_name": decision.get("tool_name"),
                "result": None,
                "error": "Tool execution was not approved.",
            },
            "continue_tool_loop": False,
        }

    tool_result = execute_tool_decision(decision)

    tool_calls = state.get("tool_calls", 0) + 1

    results = list(state.get("results", []))

    results.append(
        {
            "agent": "tool",
            "task": state.get("task", ""),
            "output": str(tool_result.get("result")),
            "tool_used": tool_result,
        }
    )

    print("\n===== APPROVED TOOL EXECUTION =====")
    print(tool_result)
    print("===================================\n")

    return {
        "results": results,
        "tool_result": tool_result,
        "tool_calls": tool_calls,
        "requires_human": False,
        "continue_tool_loop": False,
    }