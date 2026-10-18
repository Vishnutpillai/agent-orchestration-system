
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from app.agents.human_review_agent import human_review_node


def make_review_graph():
    builder = StateGraph(dict)
    builder.add_node("human_review", human_review_node)
    builder.add_edge(START, "human_review")
    builder.add_edge("human_review", END)
    return builder.compile(checkpointer=MemorySaver())


def test_human_review_pauses_for_approval():
    graph = make_review_graph()
    config = {"configurable": {"thread_id": "review-test-1"}}

    result = graph.invoke(
        {
            "task": "Create a Python file",
            "requires_human": True,
            "escalation_reason": "Approval required before file write.",
            "approval_level": "approve_action",
        },
        config=config,
    )

    assert result.get("__interrupt__")
    assert graph.get_state(config).next == ("human_review",)


def test_human_review_accepts_explicit_approval():
    graph = make_review_graph()
    config = {"configurable": {"thread_id": "review-test-2"}}

    graph.invoke(
        {
            "task": "Create a Python file",
            "requires_human": True,
            "escalation_reason": "Approval required before file write.",
            "approval_level": "approve_action",
        },
        config=config,
    )

    result = graph.invoke(
        Command(resume={"decision": "approve", "feedback": "Approved."}),
        config=config,
    )

    assert result["human_decision"] == "approved"
    assert result["requires_human"] is False


def test_human_review_rejects_explicit_rejection():
    graph = make_review_graph()
    config = {"configurable": {"thread_id": "review-test-3"}}

    graph.invoke(
        {
            "task": "Create a Python file",
            "requires_human": True,
            "escalation_reason": "Approval required before file write.",
            "approval_level": "approve_action",
        },
        config=config,
    )

    result = graph.invoke(
        Command(resume={"decision": "reject", "feedback": "Not allowed."}),
        config=config,
    )

    assert result["human_decision"] == "rejected"
    assert result["requires_human"] is False

def test_rejected_action_does_not_execute_tool(monkeypatch):
    from app.agents import approved_tool_agent

    def forbidden_execution(_decision):
        raise AssertionError("Rejected tool must not execute")

    monkeypatch.setattr(
        approved_tool_agent,
        "execute_tool_decision",
        forbidden_execution,
    )

    result = approved_tool_agent.execute_approved_tool_node(
        {
            "task": "Write a file",
            "human_decision": "rejected",
            "tool_decision": {
                "use_tool": True,
                "tool_name": "file_write",
                "arguments": {
                    "path": "should_not_exist.txt",
                    "content": "must not be written",
                },
            },
            "results": [],
        }
    )

    assert result["tool_result"]["used"] is False
    assert result["tool_result"]["error"] == (
        "Tool execution was not approved."
    )
    assert result["results"][-1]["status"] == "failed"
