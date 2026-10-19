
from app.main import TaskRequest
import pytest


def test_task_request_rejects_empty_task():
    with pytest.raises(Exception):
        TaskRequest(task="")


def test_task_request_rejects_task_over_limit():
    with pytest.raises(Exception):
        TaskRequest(task="x" * 10001)
