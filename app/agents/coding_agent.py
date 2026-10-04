from app.core.llm import get_llm


def coding_agent_node(state):

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    task = plan[current_step]["description"]

    llm = get_llm()

    results = state.get("results", [])

    previous_results = "\n\n".join(
        f"{r.get('agent', '')}: {r.get('output', '')[:700]}"
        for r in results
    )

    prompt = f"""
You are the coding specialist.

Complete this task:

{task}

Previous specialist outputs:

{previous_results}

Use relevant previous outputs when the task depends on them.

Provide a short, complete, runnable Python example when code is requested.
Keep the code under 40 lines.
Explain the important part in 2-3 sentences.
Do not add unnecessary detail.
"""

    response = llm.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are a concise Python coding specialist.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=700,
    )

    print(
        f"[CODING] finish_reason={response.choices[0].finish_reason}"
    )

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError(
            "Coding agent received an empty response from Groq."
        )

    result = {
        "agent": "coding",
        "task": task,
        "output": output,
        "status": "completed",
    }

    return {
        "results": [result],
        "current_step": current_step + 1,
    }