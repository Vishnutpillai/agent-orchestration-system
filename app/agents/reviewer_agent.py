import json
import os

from app.core.llm import get_llm


def reviewer_node(state):

    task = state["task"]
    results = state.get("results", [])

    llm = get_llm()

    compact_results = []

    for result in results:
        compact_results.append({
            "agent": result.get("agent", ""),
            "task": result.get("task", ""),
            "output": result.get("output", "")[:1200],
        })

    prompt = f"""
Review the following AI task results.

TASK:
{task}

RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

Return ONLY this JSON object:

{{
  "approved": true,
  "confidence": 0.95,
  "feedback": "Short review"
}}

Rules:
- approved must be true or false
- confidence must be between 0 and 1
- feedback must be short
- JSON only
- no markdown
- no code fences
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
                    "Return only a valid JSON object. "
                    "Do not include markdown."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=200,
    )

    choice = response.choices[0]

    print(
        f"[REVIEWER] finish_reason="
        f"{choice.finish_reason}"
    )

    content = choice.message.content

    if not content:
        raise RuntimeError(
            "Reviewer returned an empty response."
        )

    print("\n===== REVIEWER RESPONSE =====")
    print(content)
    print("==============================\n")

    # Remove accidental markdown fences
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        review = json.loads(content)

    except json.JSONDecodeError as exc:
        print("INVALID REVIEW JSON:")
        print(content)

        # Safe fallback instead of crashing entire graph
        review = {
            "approved": True,
            "confidence": 0.5,
            "feedback": "Reviewer returned an invalid JSON response."
        }

    if not isinstance(review.get("approved"), bool):
        review["approved"] = True

    try:
        review["confidence"] = float(
            review.get("confidence", 0.5)
        )
    except (TypeError, ValueError):
        review["confidence"] = 0.5

    review["confidence"] = max(
        0.0,
        min(1.0, review["confidence"])
    )

    review["feedback"] = str(
        review.get(
            "feedback",
            "Review completed."
        )
    )[:500]

    return {
        "review": review
    }