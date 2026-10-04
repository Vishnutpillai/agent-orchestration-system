import json
import os

from app.core.llm import get_llm


def reviewer_node(state):

    task = state["task"]
    results = state.get("results", [])

    llm = get_llm()

    compact_results = []

    for result in results:
        output = result.get("output", "")

        compact_results.append({
            "agent": result.get("agent", ""),
            "task": result.get("task", ""),
            "output": output[:2000],
        })

    prompt = f"""
You are the reviewer of a multi-agent AI orchestration system.

Review the specialist outputs for the user's task.

USER TASK:
{task}

SPECIALIST RESULTS:
{json.dumps(compact_results, ensure_ascii=False)}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "approved": true,
  "confidence": 0.95,
  "feedback": "Short review"
}}

Rules:

- approved must be true or false
- confidence must be a number between 0 and 1
- feedback must be short
- Do not use markdown
- Do not use ```json
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
                    "You are a strict and concise reviewer. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=300,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Reviewer received an empty response from Groq."
        )

    print("\n===== REVIEWER RESPONSE =====")
    print(content)
    print("==============================\n")

    try:
        review = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Reviewer returned invalid JSON."
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