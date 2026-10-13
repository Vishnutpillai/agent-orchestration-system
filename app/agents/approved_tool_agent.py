from app.tools.tool_agent import execute_tool_decision


def execute_approved_tool_node(state):
    """
    Execute a tool only after human approval.
    Record both successful and failed outcomes explicitly.
    """

    decision = state.get("tool_decision", {})
    results = list(state.get("results", []))
    task = state.get("task", "")

    # --------------------------------------------------------
    # HUMAN REJECTED OR DID NOT APPROVE THE ACTION
    # --------------------------------------------------------

    if state.get("human_decision") != "approved":
        tool_result = {
            "used": False,
            "tool_name": decision.get("tool_name"),
            "result": None,
            "error": "Tool execution was not approved.",
        }

        results.append(
            {
                "agent": "tool",
                "task": task,
                "output": "Tool execution failed: action not approved.",
                "status": "failed",
                "tool_used": tool_result,
            }
        )

        return {
            "results": results,
            "tool_result": tool_result,
            "continue_tool_loop": False,
            "requires_human": False,
        }

    # --------------------------------------------------------
    # EXECUTE APPROVED TOOL
    # --------------------------------------------------------

    tool_result = execute_tool_decision(decision)
    tool_calls = state.get("tool_calls", 0) + 1

    if tool_result.get("error"):
        output = (
            f"Tool execution failed: {tool_result['error']}"
        )
        status = "failed"
    else:
        output = str(tool_result.get("result"))
        status = "success"

    results.append(
        {
            "agent": "tool",
            "task": task,
            "output": output,
            "status": status,
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