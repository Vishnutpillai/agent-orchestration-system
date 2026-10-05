import json
import os

from app.core.llm import get_llm


def final_agent_node(state):

    task = state["task"]
    results = state.get("results", [])
    review = state.get("review", {})

    llm = get_llm()

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    compact_results = []

    for result in results:

        compact_results.append({
            "agent": result.get("agent", ""),
            "task": result.get("task", ""),
            "output": result.get("output", "")[:3000],
        })

    approved = review.get("approved", True)

    if approved:

        review_instruction = """
The reviewer approved the specialist results.

Create the best final answer using the available results.
"""

    else:

        review_instruction = """
The reviewer did NOT approve the specialist results.

Do not pretend that the task is fully completed.

Clearly explain what is missing or needs improvement based on
the review feedback.

If the available results are still useful, provide them while
clearly identifying the limitation.
"""

    prompt = f"""
You are the final response writer in a multi-agent AI system.

USER TASK:
{task}

SPECIALIST RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

REVIEW:
{json.dumps(review, ensure_ascii=False)}

REVIEW STATUS:
approved = {approved}

{review_instruction}

Instructions:

1. Answer the user's original task directly.
2. Use the useful information from the specialist results.
3. Respect the reviewer decision.
4. Do not claim something is complete if the reviewer rejected it.
5. Do not mention internal agent names.
6. Do not mention LangGraph or orchestration internals.
7. Do not invent information.
8. Preserve useful Python code when provided.
9. Use clear headings and code blocks where appropriate.
10. Keep the answer concise but useful.
"""

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional final-answer writer. "
                    "Produce accurate, useful answers and respect "
                    "the quality-control review."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=1800,
    )

    print(
        f"[FINAL] finish_reason="
        f"{response.choices[0].finish_reason}"
    )

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError(
            "Final agent returned an empty response."
        )

    return {
        "final_response": output
    }