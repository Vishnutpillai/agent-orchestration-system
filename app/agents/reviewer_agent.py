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
Review the specialist outputs for this task.

TASK:
{task}

RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

Return ONLY JSON:

{{
  "approved": true,
  "confidence": 0.95,
  "feedback": "Short review"
}}

Rules:
- approved: boolean
- confidence: number from 0 to 1
- feedback: short
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
                    "Return only a small valid JSON object. "
                    "Do not explain your reasoning."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=600,
        response_format={
            "type": "json_object"
        },
    )

    choice = response.choices[0]

    print(
        f"[REVIEWER] finish_reason="
        f"{choice.finish_reason}"
    )

    content = choice.message.content

    if not content:
        raise RuntimeError(
            f"Reviewer returned an empty response. "
            f"finish_reason={choice.finish_reason}"
        )

    print("\n===== REVIEWER RESPONSE =====")
    print(content)
    print("==============================\n")

    try:
        review = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Reviewer returned invalid JSON: {content}"
        ) from exc

    if "approved" not in review:
        raise RuntimeError(
            "Reviewer response is missing 'approved'."
        )

    if "confidence" not in review:
        raise RuntimeError(
            "Reviewer response is missing 'confidence'."
        )

    if "feedback" not in review:
        raise RuntimeError(
            "Reviewer response is missing 'feedback'."
        )

    if not isinstance(review["approved"], bool):
        raise RuntimeError(
            "Reviewer 'approved' must be boolean."
        )

    try:
        confidence = float(review["confidence"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "Reviewer 'confidence' must be a number."
        ) from exc

    if not 0 <= confidence <= 1:
        raise RuntimeError(
            "Reviewer 'confidence' must be between 0 and 1."
        )

    review["confidence"] = confidence

    return {
        "review": review
    }