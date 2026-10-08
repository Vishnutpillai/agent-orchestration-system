from app.memory.memory_store import save_memory


def memory_save_node(state):
    task = state.get("task", "")
    final_response = state.get("final_response", "")
    review = state.get("review", {})

    if not task:
        return {}

    save_memory({
        "task": task,
        "result": final_response,
        "review": review,
    })

    print("\n===== MEMORY SAVED =====")
    print(f"Task: {task}")
    print("========================\n")

    return {}