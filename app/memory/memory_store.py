import json
import os
from datetime import datetime


MEMORY_FILE = "app/data/memory.json"


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_memory(memory):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

    memories = _load_memory()

    memory["timestamp"] = datetime.utcnow().isoformat()

    memories.append(memory)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            memories,
            file,
            indent=2,
            ensure_ascii=False
        )


def get_memories():
    return _load_memory()


def search_memory(task, limit=5):
    memories = _load_memory()

    task_words = set(task.lower().split())

    scored = []

    for memory in memories:

        memory_task = memory.get("task", "").lower()
        memory_words = set(memory_task.split())

        score = len(task_words.intersection(memory_words))

        if score > 0:
            scored.append(
                (score, memory)
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        memory
        for _, memory in scored[:limit]
    ]