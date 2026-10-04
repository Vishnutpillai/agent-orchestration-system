import os

from app.core.llm import get_llm


def synthesizer_node(state):

    task = state["task"]
    results = state.get("results", [])
    review = state.get("review", {})

    llm = get_llm()

    compact_results = []

    for result in results:
        compact_results.append(
            {
                "agent": result.get("agent", ""),
                "task": result.get("task", ""),
                "output": result.get("output", "")[:1800],
            }
        )

    prompt = f"""
You are the final answer synthesizer.

Create one complete answer for the user's task.

USER TASK:
{task}

SPECIALIST RESULTS:
{compact_results}

REVIEW:
{review}

Requirements:

1. Answer every part of the user's task.
2. Use the specialist results as source material.
3. Fix obvious incomplete sections.
4. Do not mention internal agents.
5. Do not mention the review process.
6. Do not invent missing facts.
7. If code is requested, provide complete runnable code.
8. Keep the answer clear and well structured.
"""

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a final answer writer. "
                    "Return only the final user-facing answer."
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

    final_response = response.choices[0].message.content

    if not final_response:
        raise RuntimeError(
            "Synthesizer received an empty response from Groq."
        )

    return {
        "final_response": final_response
    }