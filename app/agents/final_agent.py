
import json
import os

from app.core.llm import get_llm


def final_agent_node(state):
    task = state.get("task", "")
    results = state.get("results", [])
    review = state.get("review", {})

    # Keep the final prompt compact.
    compact_results = []

    for result in results:
        if not isinstance(result, dict):
            continue

        compact_results.append({
            "agent": str(result.get("agent", "")),
            "task": str(result.get("task", ""))[:300],
            "output": str(result.get("output", ""))[:1200],
        })

    # File-reading tasks can return the actual file contents directly.
    task_lower = task.lower()
    is_file_read = (
        "read the contents of" in task_lower
        or "read the content of" in task_lower
        or "read readme" in task_lower
        or "read file" in task_lower
    )

    for result in results:
        if not isinstance(result, dict):
            continue

        tool_used = result.get("tool_used") or {}

        if (
            is_file_read
            and tool_used.get("tool_name") == "file_read"
            and tool_used.get("used") is True
            and not tool_used.get("error")
        ):
            content = tool_used.get("result")

            if content:
                return {
                    "final_response": str(content)
                }

    # For other tasks, ask the model to synthesize the results.
    llm = get_llm()
    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    approved = review.get("approved", True)

    prompt = f"""
Answer the user's original task using the available results.

USER TASK:
{task}

SPECIALIST RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

REVIEW:
{json.dumps(review, ensure_ascii=False)}

Reviewer approved: {approved}

Rules:
- Answer directly and accurately.
- Do not invent missing information.
- If the reviewer rejected the results, explain the limitations.
- Preserve useful code when relevant.
- Do not mention internal agent names or orchestration details.
- Keep the answer concise.
"""

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Provide a concise, useful final answer. "
                    "Never invent facts or claim incomplete work "
                    "is complete."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=1200,
    )

    choice = response.choices[0]
    output = choice.message.content

    print(f"[FINAL] finish_reason={choice.finish_reason}")

    if not output or not output.strip():
        raise RuntimeError(
            "Final agent returned an empty response. "
            f"finish_reason={choice.finish_reason}"
        )

    return {
        "final_response": output.strip()
    }
