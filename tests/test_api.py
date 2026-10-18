
from app import config
from fastapi.testclient import TestClient

from app.main import app
from app.core import graph


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_run_returns_expected_response_shape(monkeypatch):
    def fake_invoke(state, config=None):
        assert config["recursion_limit"] == 25
        assert config["configurable"]["thread_id"]
        return {
            "plan": [],
            "results": [{"content": "Example result"}],
            "review": {"status": "approved"},
            "final_response": "Machine learning finds patterns in data.",
        }

    monkeypatch.setattr(graph.agent_graph, "invoke", fake_invoke)

    response = client.post(
        "/run",
        json={"task": "Explain machine learning"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["task"] == "Explain machine learning"
    assert body["plan"] == []
    assert body["results"] == [{"content": "Example result"}]
    assert body["review"] == {"status": "approved"}
    assert body["final_response"] == (
        "Machine learning finds patterns in data."
    )


def test_run_handles_workflow_failure(monkeypatch):
    def failing_invoke(state, config=None):
        raise RuntimeError("Sensitive internal error")

    monkeypatch.setattr(graph.agent_graph, "invoke", failing_invoke)

    response = client.post(
        "/run",
        json={"task": "Explain machine learning"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The agent workflow could not complete this task. "
        "Please try again later."
    )
    assert "Sensitive internal error" not in response.text


def test_run_rejects_empty_task():
    response = client.post("/run", json={"task": ""})

    assert response.status_code == 422


def test_run_rejects_whitespace_task():
    response = client.post("/run", json={"task": "   "})

    assert response.status_code == 422


def test_run_rejects_oversized_task():
    response = client.post("/run", json={"task": "x" * 10001})

    assert response.status_code == 422


def test_tools_endpoint():
    response = client.get("/tools")

    assert response.status_code == 200
    assert isinstance(response.json()["tools"], list)

