import os

from app.core.llm import get_llm


def coding_agent_node(state):

    task = state["task"]

    plan = state.get("plan", [])
    results = state.get("results", [])

    llm = get_llm()

    previous_context = []

    for result in results:
        previous_context.append({
            "agent": result.get("agent", ""),
            "task": result.get("task", ""),
            "output": result.get("output", "")[:1500],
        })

    prompt = f"""
You are the coding specialist in a multi-agent AI system.

USER TASK:
{task}

PLAN:
{plan}

PREVIOUS AGENT RESULTS:
{previous_context}

Create a concise, correct Python solution for the coding task.

Requirements:

- Use Python.
- Prefer standard libraries and scikit-learn where appropriate.
- Include only the important code.
- Explain the approach briefly.
- Avoid unnecessary long explanations.
- Do not invent dataset-specific columns unless clearly stated.
- Avoid target leakage.
- Make the code logically executable.
- Keep the response concise.
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
                    "You are a concise Python machine learning "
                    "coding specialist."
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

    message = response.choices[0].message
    content = message.content

    finish_reason = response.choices[0].finish_reason

    print(f"[CODING] finish_reason={finish_reason}")

    if not content:
        raise RuntimeError(
            f"Coding agent received an empty response from Groq. "
            f"finish_reason={finish_reason}"
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