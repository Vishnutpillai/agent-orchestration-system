
import json
import os
import re
from datetime import datetime, timezone

MEMORY_FILE = "app/data/memory.json"


def _normalize_task(task):
    """Normalize task text for duplicate detection and search."""
    return " ".join(
        re.findall(r"\w+", str(task).lower())
    )


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_memory(memory):
    """Save a memory without adding duplicate task entries."""
    if not isinstance(memory, dict):
        raise TypeError("memory must be a dictionary")

    task = memory.get("task", "")
    normalized_task = _normalize_task(task)

    if not normalized_task:
        return

    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    memories = _load_memory()

    # Keep one entry per normalized task.
    for existing in memories:
        if _normalize_task(existing.get("task", "")) == normalized_task:
            # Update the existing entry with new information.
            existing.update(memory)
            existing["timestamp"] = datetime.now(
                timezone.utc
            ).isoformat()

            with open(MEMORY_FILE, "w", encoding="utf-8") as file:
                json.dump(memories, file, indent=2, ensure_ascii=False)
            return

    new_memory = memory.copy()
    new_memory["timestamp"] = datetime.now(
        timezone.utc
    ).isoformat()
    memories.append(new_memory)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memories, file, indent=2, ensure_ascii=False)


def get_memories():
    return _load_memory()


def search_memory(task, limit=5):
    """Return distinct, relevant memories ranked by word overlap."""
    if limit <= 0:
        return []

    normalized_task = _normalize_task(task)
    task_words = set(normalized_task.split())

    if not task_words:
        return []

    memories = _load_memory()
    scored = []
    seen_tasks = set()

    for memory in memories:
        if not isinstance(memory, dict):
            continue

        memory_task = memory.get("task", "")
        normalized_memory_task = _normalize_task(memory_task)

        if not normalized_memory_task:
            continue

        # Avoid duplicate results, including duplicates already in memory.json.
        if normalized_memory_task in seen_tasks:
            continue
        seen_tasks.add(normalized_memory_task)

        memory_words = set(normalized_memory_task.split())
        overlap = len(task_words.intersection(memory_words))

        if overlap == 0:
            continue

        # Normalize score so short and long tasks are more comparable.
        score = overlap / len(task_words.union(memory_words))
        scored.append((score, memory))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [memory for _, memory in scored[:limit]]
