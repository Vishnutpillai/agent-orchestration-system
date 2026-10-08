
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

from app.memory.memory_node import memory_retrieval_node
from app.memory.memory_save_node import memory_save_node
from app.agents.approved_tool_agent import execute_approved_tool_node


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

    # -----------------------------------------------------
    # ADD ALL NODES
    # -----------------------------------------------------

    graph.add_node("memory", memory_retrieval_node)

    graph.add_node("supervisor", supervisor_node)

    graph.add_node("research", run_research)

    graph.add_node("data", run_data)

    graph.add_node("coding", run_coding)

    graph.add_node("tool_loop", tool_loop_node)

    graph.add_node("reviewer", reviewer_node)

    graph.add_node("human_review", human_review_node)

    graph.add_node("approved_tool",execute_approved_tool_node)

    graph.add_node("final", final_agent_node)

    graph.add_node("memory_save", memory_save_node)

    # -----------------------------------------------------
    # START → MEMORY
    # -----------------------------------------------------

    graph.add_edge(
        START,
        "memory"
    )

    # -----------------------------------------------------
    # MEMORY → SUPERVISOR
    # -----------------------------------------------------

    graph.add_edge(
        "memory",
        "supervisor"
    )

    # -----------------------------------------------------
    # SUPERVISOR ROUTING
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "research": "research",
            "data": "data",
            "coding": "coding",
            "reviewer": "reviewer",
        },
    )

    # -----------------------------------------------------
    # RESEARCH ROUTING
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "research",
        route_after_agent,
        {
            "research": "research",
            "data": "data",
            "coding": "coding",
            "reviewer": "reviewer",
        },
    )

    # -----------------------------------------------------
    # DATA ROUTING
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "data",
        route_after_agent,
        {
            "research": "research",
            "data": "data",
            "coding": "coding",
            "reviewer": "reviewer",
        },
    )

    # -----------------------------------------------------
    # CODING → TOOL LOOP
    # -----------------------------------------------------

    graph.add_edge(
        "coding",
        "tool_loop"
    )

    # -----------------------------------------------------
    # TOOL LOOP ROUTING
    # -----------------------------------------------------

    graph.add_conditional_edges(
    "tool_loop",
    route_after_tool,
    {
        "tool_loop": "tool_loop",
        "human_review": "human_review",
        "reviewer": "reviewer",
    },
    )
    # -----------------------------------------------------
    # HUMAN REVIEW → REVIEWER
    # -----------------------------------------------------

    graph.add_edge(
    "human_review",
    "approved_tool"
    )

    # -----------------------------------------------------
# APPROVED TOOL → REVIEWER
# -----------------------------------------------------

    graph.add_edge(
    "approved_tool",
    "reviewer"
    )

    # -----------------------------------------------------
    # REVIEWER → FINAL
    # -----------------------------------------------------

    graph.add_edge(
        "reviewer",
        "final"
    )

    # -----------------------------------------------------
    # FINAL → MEMORY SAVE
    # -----------------------------------------------------

    graph.add_edge(
        "final",
        "memory_save"
    )

    # -----------------------------------------------------
    # MEMORY SAVE → END
    # -----------------------------------------------------

    graph.add_edge(
        "memory_save",
        END
    )

    # -----------------------------------------------------
    # COMPILE
    # -----------------------------------------------------

    return graph.compile()


# =========================================================
# COMPILED GRAPH
# =========================================================

agent_graph = build_graph()