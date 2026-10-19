
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unknown_run_returns_404():
    response = client.get(
        "/runs/unknown-thread-id"
    )

    assert response.status_code == 404


def test_completed_run_status():
    run_response = client.post(
        "/run",
        json={
            "task": "Explain how machine learning works"
        },
    )

    assert run_response.status_code == 200

    run_data = run_response.json()
    thread_id = run_data["thread_id"]

    status_response = client.get(
        f"/runs/{thread_id}"
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["thread_id"] == thread_id
    assert status_data["status"] == "completed"
    assert status_data["task"] == (
        "Explain how machine learning works"
    )
    assert status_data["next_nodes"] == []
