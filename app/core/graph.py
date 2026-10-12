import re

from langgraph.graph import StateGraph, START, END

from app.core.state import AgentState

from app.agents.supervisor import supervisor_node
from app.agents.research_agent import research_agent_node
from app.agents.data_agent import data_agent_node
from app.agents.coding_agent import coding_agent_node
from app.agents.tool_loop_agent import tool_loop_node
from app.agents.reviewer_agent import reviewer_node
from app.agents.final_agent import final_agent_node
from app.agents.human_review_agent import human_review_node
from app.agents.approved_tool_agent import execute_approved_tool_node

from app.memory.memory_node import memory_retrieval_node
from app.memory.memory_save_node import memory_save_node


def get_direct_tool_request(task):
    """Detect tasks that should enter the tool workflow directly."""
    task = task.lower().strip()

    read_phrases = (
        "read the contents of",
        "read the content of",
        "read file",
        "read the file",
        "read readme",
    )

    write_phrases = (
        "write the text",
        "write the string",
        "write to file",
        "write to a file",
        "write a file",
        "create a file",
        "save to a file",
    )

    calculation_phrases = (
        "calculate",
        "compute",
        "divided by",
        "multiplied by",
        "division",
        "subtract",
        "multiply",
        "percentage",
    )

    if any(p in task for p in read_phrases + write_phrases):
        return True

    if any(p in task for p in calculation_phrases):
        return True

    if re.search(r"\b\d+\s*[-+*/]\s*\d+\b", task):
        return True

    return False


# =========================================================
# SPECIALIST NODE WRAPPERS
# =========================================================

def run_research(state):
    result = research_agent_node(state)

    return {
        **result,
        "current_step": state.get("current_step", 0) + 1,
    }


def run_data(state):
    result = data_agent_node(state)

    return {
        **result,
        "current_step": state.get("current_step", 0) + 1,
    }


def run_coding(state):
    result = coding_agent_node(state)

    return {
        **result,
        "current_step": state.get("current_step", 0) + 1,
        "tool_calls": 0,
        "continue_tool_loop": True,
    }


# =========================================================
# SUPERVISOR ROUTING
# =========================================================

def route_from_supervisor(state):
    task = state.get("task", "")

    # Direct calculator and file requests bypass specialist LLM calls.
    if get_direct_tool_request(task):
        return "tool_loop"

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step].get("specialist")

    if specialist not in {"research", "data", "coding"}:
        return "research"

    return specialist


# =========================================================
# SPECIALIST ROUTING
# =========================================================

def route_after_agent(state):
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step].get("specialist")

    if specialist not in {"research", "data", "coding"}:
        return "research"

    return specialist


# =========================================================
# TOOL LOOP ROUTING
# =========================================================

def route_after_tool(state):
    if state.get("continue_tool_loop", False):
        return "tool_loop"

    if state.get("requires_human", False):
        return "human_review"

    return "reviewer"


# =========================================================
# BUILD GRAPH
# =========================================================

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("memory", memory_retrieval_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", run_research)
    graph.add_node("data", run_data)
    graph.add_node("coding", run_coding)
    graph.add_node("tool_loop", tool_loop_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("approved_tool", execute_approved_tool_node)
    graph.add_node("final", final_agent_node)
    graph.add_node("memory_save", memory_save_node)

    graph.add_edge(START, "memory")
    graph.add_edge("memory", "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "research": "research",
            "data": "data",
            "coding": "coding",
            "tool_loop": "tool_loop",
            "reviewer": "reviewer",
        },
    )

    for specialist_node in ("research", "data"):
        graph.add_conditional_edges(
            specialist_node,
            route_after_agent,
            {
                "research": "research",
                "data": "data",
                "coding": "coding",
                "reviewer": "reviewer",
            },
        )

    graph.add_edge("coding", "tool_loop")

    graph.add_conditional_edges(
        "tool_loop",
        route_after_tool,
        {
            "tool_loop": "tool_loop",
            "human_review": "human_review",
            "reviewer": "reviewer",
        },
    )

    graph.add_edge("human_review", "approved_tool")
    graph.add_edge("approved_tool", "reviewer")
    graph.add_edge("reviewer", "final")
    graph.add_edge("final", "memory_save")
    graph.add_edge("memory_save", END)

    return graph.compile()


agent_graph = build_graph()
