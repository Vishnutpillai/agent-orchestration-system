from langgraph.graph import StateGraph, START, END

from app.core.state import AgentState

from app.agents.supervisor import supervisor_node
from app.agents.research_agent import research_agent_node
from app.agents.data_agent import data_agent_node
from app.agents.coding_agent import coding_agent_node
from app.agents.reviewer_agent import reviewer_node
from app.agents.final_agent import final_agent_node


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
    }


def route_from_supervisor(state):

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step].get("specialist")

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

    if current_step >= len(plan):
        return "reviewer"

    specialist = plan[current_step].get("specialist")

    if specialist not in {
        "research",
        "data",
        "coding",
    }:
        return "research"

    return specialist


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_node(
        "research",
        run_research,
    )

    graph.add_node(
        "data",
        run_data,
    )

    graph.add_node(
        "coding",
        run_coding,
    )

    graph.add_node(
        "reviewer",
        reviewer_node,
    )

    graph.add_node(
        "final",
        final_agent_node,
    )

    graph.add_edge(
        START,
        "supervisor",
    )

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

    graph.add_edge(
        "reviewer",
        "final",
    )

    graph.add_edge(
        "final",
        END,
    )

    return graph.compile()


agent_graph = build_graph()