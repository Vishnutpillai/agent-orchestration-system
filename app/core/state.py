from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):

    # Original user request
    task: str

    # Supervisor-generated execution plan
    plan: List[Dict[str, Any]]

    # Agent currently selected
    selected_agent: str

    # Results produced by specialist agents
    results: List[Dict[str, Any]]

    # Reviewer decision
    review: Dict[str, Any]

    # Final response
    final_response: str

    # Current supervisor plan step
    current_step: int

    # Tool execution state
    tool_decision: Dict[str, Any]
    tool_result: Dict[str, Any]

    # Tool-call control
    tool_calls: int
    max_tool_calls: int
    continue_tool_loop: bool

    # Memory
    memories: List[Dict[str, Any]]

    # Human-in-the-loop state
    requires_human: bool
    escalation_reason: str
    approval_level: str
    human_decision: str
    human_feedback: str