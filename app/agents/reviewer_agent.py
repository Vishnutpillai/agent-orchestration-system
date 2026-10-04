from app.core.llm import get_llm
import json


def reviewer_node(state):

    results = state.get("results", [])

    llm = get_llm()

    # Keep the reviewer input small.
    # We only need enough information to judge each specialist output.
    compact_results = []

    for r in results:
        compact_results.append(
            {
                "agent": r.get("agent", ""),
                "task": r.get("task", ""),
                "output": r.get("output", "")[:1800],
            }
        )

    results_text = json.dumps(
        compact_results,
        ensure_ascii=False,
    )

    prompt = f"""
You are the reviewer agent in a multi-agent AI system.

Review the specialist outputs below.

SPECIALIST OUTPUTS:
{results_text}

Your job:
1. Check whether every specialist completed its assigned task.
2. Check whether the answers are useful and coherent.
3. Check whether the coding answer is reasonably complete.
4. Give concise feedback.
5. Return ONLY valid JSON.

The JSON MUST have exactly these fields:

{{
  "approved": true,
  "confidence": 0.9,
  "feedback": "Short review feedback"
}}

Rules:
- approved must be true or false.
- confidence must be a number between 0 and 1.
- feedback must be a short string.
- Do NOT use markdown.
- Do NOT use code fences.
- Do NOT add any other fields.
- Keep the JSON very short.
"""

    response = llm.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are a strict but concise output reviewer. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.0,
        max_tokens=200,
        response_format={
            "type": "json_object"
        },
    )

    print(
        f"[REVIEWER] finish_reason="
        f"{response.choices[0].finish_reason}"
    )

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError(
            "Reviewer received an empty response from Groq."
        )

    try:
        review = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Reviewer returned invalid JSON: {output}"
        ) from exc

    # Defensive defaults
    approved = bool(review.get("approved", False))
    confidence = float(review.get("confidence", 0.0))
    feedback = str(review.get("feedback", ""))

    return {
        "review": {
            "approved": approved,
            "confidence": confidence,
            "feedback": feedback,
        }
    }