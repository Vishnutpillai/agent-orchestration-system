
from app.memory.memory_store import (
    get_memories,
    save_memory,
    search_memory,
)


def test_save_memory():
    task = "Test task for memory saving"

    save_memory({
        "task": task,
        "result": "Test result",
    })

    memories = get_memories()

    matching = [
        memory for memory in memories
        if memory.get("task") == task
    ]

    assert len(matching) == 1
    assert matching[0]["result"] == "Test result"
    assert "timestamp" in matching[0]


def test_search_memory():
    task = "Unique memory search verification task"

    save_memory({
        "task": task,
        "result": "Search test result",
    })

    results = search_memory(task, limit=5)

    assert any(
        memory.get("task") == task
        for memory in results
    )
