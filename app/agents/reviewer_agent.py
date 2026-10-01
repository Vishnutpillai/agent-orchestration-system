from app.core.llm import get_llm
import json


# ---------------------------------------------------------
# Helper: keep reviewer context small
# ---------------------------------------------------------
def compact_text(text, max_chars=2200):
    """
    Keep only a compact portion of long specialist output.

    This prevents the Reviewer Agent prompt from exceeding
    the Groq TPM limit.
    """

    if text is None:
        return ""

    text = str(text).strip()

    if len(text) <= max_chars:
        return text

    # Keep beginning + ending so conclusions are not lost.
    first_part = int(max_chars * 0.70)
    last_part = max_chars - first_part

    return (
        text[:first_part]
        + "\n\n...[output truncated for reviewer]...\n\n"
        + text[-last_part:]
    )


def reviewer_node(state):

    results = state.get("results", [])

    # ---------------------------------------------------------
    # No specialist results
    # ---------------------------------------------------------
    if not results:
        return {
            "review": {
                "approved": False,
                "confidence": 0.0,
                "feedback": "No specialist results were produced.",
            },
            "final_response": "No specialist results were produced.",
        }

    # ---------------------------------------------------------
    # Compact specialist outputs
    # ---------------------------------------------------------
    compact_results = []

    for result in results:

        agent_name = result.get("agent", "unknown")
        output = result.get("output", "")

        compact_output = compact_text(
            output,
            max_chars=2200
        )

        compact_results.append(
            f"""
--- Agent: {agent_name} ---

Output:
{compact_output}
"""
        )

    combined_results = "\n".join(compact_results)

    # ---------------------------------------------------------
    # Limit the original task too
    # ---------------------------------------------------------
    original_task = compact_text(
        state.get("task", ""),
        max_chars=1800
    )

    # ---------------------------------------------------------
    # Reviewer prompt
    # ---------------------------------------------------------
    prompt = f"""
You are the Reviewer Agent in a multi-agent orchestration system.

Review the specialist outputs below and determine whether they adequately
answer the original user task.

Original user task:
{original_task}

Specialist outputs:
{combined_results}

Evaluate:

- Relevance
- Completeness
- Consistency
- Clarity
- Unsupported claims
- Whether the original task was answered

Return ONLY this JSON object:

{{
    "approved": true,
    "confidence": 0.95,
    "feedback": "The combined response adequately answers the task."
}}

Rules:

- approved must be true or false.
- confidence must be a number between 0 and 1.
- feedback must be short.
- Do not use Markdown.
- Do not use code fences.
- Do not include any text before or after the JSON.
"""

    # ---------------------------------------------------------
    # Call reviewer LLM safely
    # ---------------------------------------------------------
    try:

        llm = get_llm()

        response = llm.invoke(prompt)

        content = str(response.content).strip()

    except Exception as exc:

        # Do not crash the complete orchestration pipeline
        print(
            f"Reviewer LLM error: {type(exc).__name__}: {exc}"
        )

        review = {
            "approved": True,
            "confidence": 0.5,
            "feedback": (
                "Reviewer LLM was unavailable. "
                "Specialist outputs were returned without LLM review."
            ),
        }

        final_response = "\n\n".join(
            [
                (
                    f"### {result.get('agent', 'Specialist').title()} Agent\n\n"
                    f"{result.get('output', '')}"
                )
                for result in results
            ]
        )

        return {
            "review": review,
            "final_response": final_response,
        }

    # ---------------------------------------------------------
    # Parse JSON
    # ---------------------------------------------------------
    try:

        review = json.loads(content)

    except json.JSONDecodeError:

        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end != -1 and end > start:

            try:

                review = json.loads(
                    content[start:end + 1]
                )

            except json.JSONDecodeError:

                review = {
                    "approved": False,
                    "confidence": 0.0,
                    "feedback": (
                        "Reviewer produced an invalid "
                        "structured response."
                    ),
                }

        else:

            review = {
                "approved": False,
                "confidence": 0.0,
                "feedback": (
                    "Reviewer produced an invalid "
                    "structured response."
                ),
            }

    # ---------------------------------------------------------
    # Validate reviewer fields
    # ---------------------------------------------------------
    approved = review.get("approved")

    confidence = review.get("confidence")

    feedback = review.get("feedback")

    if not isinstance(approved, bool):
        approved = False

    if not isinstance(confidence, (int, float)):
        confidence = 0.0

    confidence = max(
        0.0,
        min(1.0, float(confidence))
    )

    if not isinstance(feedback, str):
        feedback = "No reviewer feedback provided."

    review = {
        "approved": approved,
        "confidence": confidence,
        "feedback": feedback,
    }

    # ---------------------------------------------------------
    # Combine full specialist outputs for final response
    #
    # IMPORTANT:
    # We only compact the data sent to the reviewer.
    # The user still receives the full specialist outputs.
    # ---------------------------------------------------------
    final_response = "\n\n".join(
        [
            (
                f"### {result.get('agent', 'Specialist').title()} Agent\n\n"
                f"{result.get('output', '')}"
            )
            for result in results
        ]
    )

    return {
        "review": review,
        "final_response": final_response,
    }