from typing import Annotated, TypedDict, List, Dict, Any
import operator


class AgentState(TypedDict, total=False):

    # Original user request
    task: str

    # Supervisor-generated execution plan
    plan: List[Dict[str, Any]]

    # Current subtask being executed
    current_step: int

    # Agent currently selected
    selected_agent: str

    # Results from all specialist agents
    results: Annotated[
        List[Dict[str, Any]],
        operator.add
    ]

    # Reviewer result
    review: Dict[str, Any]

    # Final answer
    final_response: str