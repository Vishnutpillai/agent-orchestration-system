from app.memory.memory_store import search_memory


def memory_retrieval_node(state):

    task = state["task"]

    memories = search_memory(
        task,
        limit=5,
    )

    print("\n===== MEMORY RETRIEVAL =====")
    print(f"Found {len(memories)} relevant memories")

    for memory in memories:
        print(
            f"- {memory.get('task', '')}"
        )

    print("============================\n")

    return {
        "memories": memories
    }