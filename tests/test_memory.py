from app.memory.memory_store import (
    save_memory,
    get_memories,
    search_memory,
)


def test_save_memory():
    save_memory({
        "task": "Test task",
        "result": "Test result",
    })

    memories = get_memories()

    assert len(memories) >= 1
    assert memories[-1]["task"] == "Test task"
    assert memories[-1]["result"] == "Test result"


def test_search_memory():
    save_memory({
        "task": "Calculate 10 multiplied by 5",
        "result": "50",
    })

    results = search_memory(
        "Calculate 10 multiplied by 5"
    )

    assert len(results) >= 1
    assert results[0]["result"] == "50"