import json
import os

from app.core.llm import get_llm


def supervisor_node(state):

    task = state["task"]

    llm = get_llm()

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    prompt = f"""
You are the supervisor of a multi-agent AI orchestration system.

Your job is to divide the user's task into clear sequential subtasks.

Available specialist agents:

- research: research, explanations, concepts, information
- data: datasets, CSV, Pandas, statistics, EDA, preprocessing
- coding: Python, programming, debugging, algorithms

USER TASK:
{task}

Create the smallest useful sequential plan.

Rules:

1. Use only these specialist names:
   research
   data
   coding

2. Return ONLY valid JSON.

3. Do not use markdown.

4. Do not use ```json.

5. The JSON must have exactly this structure:

{{
  "plan": [
    {{
      "id": 1,
      "specialist": "research",
      "description": "short description",
      "required_inputs": [],
      "expected_output": "short description",
      "complexity": "low",
      "status": "pending"
    }}
  ]
}}

6. Identify every distinct deliverable requested by the user.

7. Never omit a requested deliverable.

8. If the user asks for research, explanation, or concepts, create a research step.

9. If the user asks for datasets, data analysis, statistics, EDA, or preprocessing, create a data step.

10. If the user asks for Python, programming, implementation, or debugging, create a coding step.

11. Create between 1 and 5 useful steps.

12. Preserve dependencies using required_inputs.

13. Keep each description concise.
"""

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a task-planning supervisor. "
                    "Always return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=1200,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Supervisor received an empty response from Groq."
        )

    print("\n===== SUPERVISOR RESPONSE =====")
    print(content)
    print("================================\n")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Supervisor returned invalid JSON."
        ) from exc

    if "plan" not in data:
        raise RuntimeError(
            "Supervisor JSON does not contain a 'plan' field."
        )

    plan = data["plan"]

    if not isinstance(plan, list):
        raise RuntimeError(
        "Supervisor 'plan' must be a list."
    )

    if not plan:
        raise RuntimeError(
        "Supervisor returned an empty plan."
    )

    allowed_agents = {
    "research",
    "data",
    "coding",
}

    for item in plan:

        if item.get("specialist") not in allowed_agents:
            raise RuntimeError(
                f"Invalid specialist: {item.get('specialist')}"
            )

    return {
    "plan": plan,
    "current_step": 0,
}