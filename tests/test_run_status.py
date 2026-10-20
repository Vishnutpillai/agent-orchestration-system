
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core import graph
from app.main import app

client = TestClient(app)


def test_unknown_run_returns_404():
    response = client.get("/runs/unknown-thread-id")

    assert response.status_code == 404


def test_completed_run_status(monkeypatch):
    def fake_invoke(state, config=None):
        return {
            "task": state["task"],
            "current_step": 1,
            "plan": [],
            "results": [{"content": "Example result"}],
            "review": {"status": "approved"},
            "final_response": "Machine learning finds patterns in data.",
        }

    def fake_get_state(config):
        thread_id = config["configurable"]["thread_id"]

        return SimpleNamespace(
            config=config,
            metadata={"source": "test"},
            values={
                "task": "Explain how machine learning works",
                "current_step": 1,
                "plan": [],
                "results": [{"content": "Example result"}],
            },
            next=(),
            tasks=(),
        )

    monkeypatch.setattr(graph.agent_graph, "invoke", fake_invoke)
    monkeypatch.setattr(graph.agent_graph, "get_state", fake_get_state)

    run_response = client.post(
        "/run",
        json={"task": "Explain how machine learning works"},
    )

    assert run_response.status_code == 200

    thread_id = run_response.json()["thread_id"]

    status_response = client.get(f"/runs/{thread_id}")

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["thread_id"] == thread_id
    assert status_data["status"] == "completed"
    assert status_data["task"] == "Explain how machine learning works"
    assert status_data["next_nodes"] == []


def test_approval_pending_run_status(monkeypatch):
    approval_request = {
        "message": "Approval is required before writing the file.",
        "tool_name": "file_write",
    }

    def fake_invoke(state, config=None):
        return {
            "task": state["task"],
            "current_step": 0,
            "plan": [],
            "results": [],
            "__interrupt__": [
                SimpleNamespace(value=approval_request)
            ],
        }

    def fake_get_state(config):
        return SimpleNamespace(
            config=config,
            metadata={"source": "test"},
            values={
                "task": (
                    "Write the text Hello from Project 15 "
                    "to approval_status_test.txt"
                ),
                "current_step": 0,
                "plan": [],
                "results": [],
            },
            next=("human_review",),
            tasks=(
                SimpleNamespace(
                    interrupts=(
                        SimpleNamespace(value=approval_request),
                    )
                ),
            ),
        )

    monkeypatch.setattr(graph.agent_graph, "invoke", fake_invoke)
    monkeypatch.setattr(graph.agent_graph, "get_state", fake_get_state)

    run_response = client.post(
        "/run",
        json={
            "task": (
                "Write the text Hello from Project 15 "
                "to approval_status_test.txt"
            )
        },
    )

    assert run_response.status_code == 200

    run_data = run_response.json()
    assert run_data["status"] == "approval_required"

    thread_id = run_data["thread_id"]

    status_response = client.get(f"/runs/{thread_id}")

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["thread_id"] == thread_id
    assert status_data["status"] == "approval_required"
    assert "human_review" in status_data["next_nodes"]
    assert status_data["approval_request"] == approval_request
