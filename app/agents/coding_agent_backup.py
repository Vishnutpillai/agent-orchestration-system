import os

from app.core.llm import get_llm


def coding_agent_node(state):

    task = state["task"]

    plan = state.get("plan", [])
    results = state.get("results", [])

    llm = get_llm()

    # Keep only useful previous context
    previous_context = []

    for result in results:
        previous_context.append({
            "agent": result.get("agent", ""),
            "output": result.get("output", "")[:1000],
        })

    prompt = f"""
You are the coding specialist.

USER TASK:
{task}

CODING REQUIREMENTS FROM PLAN:
{plan}

USEFUL PREVIOUS RESULTS:
{previous_context}

Create a concise Python solution.

Requirements:
- Use Python.
- Use scikit-learn when appropriate.
- Include executable code.
- Include only important code.
- Briefly explain the approach.
- Do not invent dataset columns unless required.
- Avoid data leakage.
- Keep the answer under 700 words.
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
                    "You are a concise Python ML coding specialist. "
                    "Return a practical solution."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=1800,
    )

    choice = response.choices[0]

    print(
        f"[CODING] finish_reason={choice.finish_reason}"
    )

    content = choice.message.content

    if not content:
        raise RuntimeError(
            f"Coding agent returned empty content. "
            f"finish_reason={choice.finish_reason}"
        )

    return {
        "results": [
            {
                "agent": "coding",
                "task": task,
                "output": content,
            }
        ]
    }