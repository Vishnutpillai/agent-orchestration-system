from langgraph.graph import StateGraph, START, END

from app.core.state import AgentState

from app.agents.supervisor import supervisor_node
from app.agents.research_agent import research_agent_node
from app.agents.data_agent import data_agent_node
from app.agents.coding_agent import coding_agent_node
from app.agents.reviewer_agent import reviewer_node


def route_from_supervisor(state):

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step]["specialist"]

    if specialist not in {
        "research",
        "data",
        "coding",
    }:
        return "research"

    return specialist


def route_after_agent(state):

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    # All subtasks completed
    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step]["specialist"]

    if specialist not in {
        "research",
        "data",
        "coding",
    }:
        return "research"

    return specialist


def build_graph():

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_node(
        "research",
        research_agent_node,
    )

    graph.add_node(
        "data",
        data_agent_node,
    )

    graph.add_node(
        "coding",
        coding_agent_node,
    )

    graph.add_node(
        "reviewer",
        reviewer_node,
    )

    # START -> Supervisor
    graph.add_edge(
        START,
        "supervisor",
    )

    # Supervisor -> first specialist
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

    # After Research
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

    # After Data
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

    # After Coding
    graph.add_conditional_edges(
        "coding",
        route_after_agent,
        {
            "research": "research",
            "data": "data",
            "coding": "coding",
            "reviewer": "reviewer",
        },
    )

    # Reviewer -> END
    graph.add_edge(
        "reviewer",
        END,
    )

    return graph.compile()


agent_graph = build_graph()