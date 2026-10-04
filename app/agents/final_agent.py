import json
import os

from app.core.llm import get_llm


def final_agent_node(state):
    task = state["task"]
    results = state.get("results", [])
    review = state.get("review", {})

    llm = get_llm()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    compact_results = []

    for result in results:
        compact_results.append({
            "agent": result.get("agent", ""),
            "task": result.get("task", ""),
            "output": result.get("output", ""),
        })

    prompt = f"""
You are the final response synthesizer in a multi-agent AI system.

Create the final answer for the user's task using the specialist results below.

USER TASK:
{task}

SPECIALIST RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

REVIEW:
{json.dumps(review, ensure_ascii=False)}

Instructions:

1. Answer the user's original task directly.
2. Combine the useful information from all specialist agents.
3. Do not mention the internal agents, supervisor, reviewer, or orchestration system.
4. Do not invent information that is not present in the specialist results.
5. Preserve Python code when provided.
6. Use clear headings, numbered steps, bullet points, and code blocks where appropriate.
7. Make the response complete but concise.
"""

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are the final answer writer for an AI orchestration system."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    print(
        f"[FINAL] finish_reason="
        f"{response.choices[0].finish_reason}"
    )

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError("Final agent returned an empty response.")

    return {
        "final_response": output
    }