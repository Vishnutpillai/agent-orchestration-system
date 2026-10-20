
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from app.agents.human_review_agent import human_review_node


def build_review_graph(checkpointer):
    builder = StateGraph(dict)

    builder.add_node("human_review", human_review_node)
    builder.add_edge(START, "human_review")
    builder.add_edge("human_review", END)

    return builder.compile(checkpointer=checkpointer)


def test_pending_approval_survives_sqlite_reopen(tmp_path):
    database_path = tmp_path / "checkpoints.sqlite"
    thread_id = "sqlite-persistence-test"
    config = {"configurable": {"thread_id": thread_id}}

    task = "Create a Python file"
    reason = "Approval required before file write."

    # Create a checkpoint and pause at human approval.
    connection = sqlite3.connect(str(database_path),check_same_thread=False,)
    saver = SqliteSaver(connection)
    saver.setup()

    graph = build_review_graph(saver)

    result = graph.invoke(
        {
            "task": task,
            "requires_human": True,
            "escalation_reason": reason,
            "approval_level": "approve_action",
        },
        config=config,
    )

    assert result.get("__interrupt__")

    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)
    assert snapshot.values["task"] == task

    # Simulate closing and reopening the application's checkpoint database.
    connection.close()

    reopened_connection = sqlite3.connect(str(database_path),check_same_thread=False,)
    reopened_saver = SqliteSaver(reopened_connection)
    reopened_saver.setup()

    reopened_graph = build_review_graph(reopened_saver)

    try:
        restored = reopened_graph.get_state(config)

        assert restored.next == ("human_review",)
        assert restored.values["task"] == task
        assert restored.values["escalation_reason"] == reason

        assert restored.tasks
        assert restored.tasks[0].interrupts

        approval_request = restored.tasks[0].interrupts[0].value
        assert approval_request["task"] == task
        assert approval_request["reason"] == reason

        # Resume the restored workflow with explicit approval.
        result = reopened_graph.invoke(
            Command(
                resume={
                    "decision": "approve",
                    "feedback": "Approved for testing.",
                }
            ),
            config=config,
        )

        assert result["human_decision"] == "approved"
        assert result["requires_human"] is False
        assert result["human_feedback"] == "Approved for testing."

        # The workflow has finished, so there should be no next node.
        completed = reopened_graph.get_state(config)
        assert completed.next == ()

    finally:
        reopened_connection.close()
