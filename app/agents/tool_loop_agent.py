from app.tools.tool_agent import choose_tool, execute_tool_decision


MAX_TOOL_CALLS = 5

# Tools that require human approval before execution
HUMAN_APPROVAL_TOOLS = {
    "file_write",
    "code_execution",
}


def tool_loop_node(state):
    """
    Select and execute one tool.

    Risky tools are paused for human approval before execution.
    """

    task = state["task"]

    results = list(state.get("results", []))

    context_parts = []

    for result in results:
        context_parts.append(
            {
                "agent": result.get("agent", ""),
                "task": result.get("task", ""),
                "output": result.get("output", "")[:2000],
                "tool_used": result.get("tool_used", {}),
            }
        )

    context = str(context_parts)

    tool_calls = state.get("tool_calls", 0)

    # -----------------------------------------------------
    # MAX TOOL CALL LIMIT
    # -----------------------------------------------------

    if tool_calls >= MAX_TOOL_CALLS:

        return {
            "continue_tool_loop": False,
            "requires_human": False,
            "tool_calls": tool_calls,
            "tool_decision": {
                "use_tool": False,
                "tool_name": None,
                "arguments": {},
                "reason": "Maximum tool-call limit reached.",
            },
            "tool_result": {
                "used": False,
                "tool_name": None,
                "result": None,
            },
        }

    # -----------------------------------------------------
    # CHOOSE TOOL
    # -----------------------------------------------------

    decision = choose_tool(
        task=task,
        context=context,
    )

    print("\n===== TOOL LOOP DECISION =====")
    print(decision)
    print("==============================\n")

    # -----------------------------------------------------
    # NO TOOL REQUIRED
    # -----------------------------------------------------

    if not decision.get("use_tool", False):

        return {
            "tool_decision": decision,
            "tool_result": {
                "used": False,
                "tool_name": None,
                "result": None,
            },
            "tool_calls": tool_calls,
            "continue_tool_loop": False,
            "requires_human": False,
        }

    # -----------------------------------------------------
    # CHECK HUMAN APPROVAL
    # -----------------------------------------------------

    tool_name = decision.get("tool_name")

    if tool_name in HUMAN_APPROVAL_TOOLS:

        print("\n===== HUMAN APPROVAL REQUIRED =====")
        print(f"Tool: {tool_name}")
        print(f"Reason: {decision.get('reason', '')}")
        print("===================================\n")

        return {
            "tool_decision": decision,
            "tool_result": {
                "used": False,
                "tool_name": tool_name,
                "result": None,
            },
            "tool_calls": tool_calls,
            "continue_tool_loop": False,
            "requires_human": True,
            "escalation_reason": (
                f"Human approval required before executing '{tool_name}'."
            ),
            "approval_level": "approve_action",
        }

    # -----------------------------------------------------
    # SAFE TOOL → EXECUTE DIRECTLY
    # -----------------------------------------------------

    tool_result = execute_tool_decision(decision)

    tool_calls += 1

    print("\n===== TOOL LOOP RESULT =====")
    print(tool_result)
    print("============================\n")

    # -----------------------------------------------------
    # ADD TOOL RESULT TO SHARED RESULTS
    # -----------------------------------------------------

    results.append(
        {
            "agent": "tool",
            "task": task,
            "output": str(tool_result.get("result")),
            "tool_used": tool_result,
        }
    )

    return {
        "results": results,
        "tool_decision": decision,
        "tool_result": tool_result,
        "tool_calls": tool_calls,
        "continue_tool_loop": False,
        "requires_human": False,
    }