import json

from app.core.llm import get_llm


SUPERVISOR_PROMPT = """
You are the Supervisor Agent in a multi-agent orchestration system.

Your job is to analyze the user's task and create a structured execution plan.

Available specialist agents:

1. research
   - Research
   - Information gathering
   - Explanations
   - Knowledge retrieval

2. data
   - CSV analysis
   - Pandas
   - Statistics
   - Data processing
   - Data visualization

3. coding
   - Python
   - Programming
   - Debugging
   - Algorithms
   - Code generation

Rules:

- Break complex tasks into logical subtasks.
- Use multiple specialists when necessary.
- Keep simple tasks to one specialist.
- Order subtasks logically.
- Return ONLY valid JSON.

JSON format:

{{
    "plan": [
        {{
            "id": 1,
            "specialist": "research",
            "description": "subtask description",
            "required_inputs": ["user_task"],
            "expected_output": "expected result",
            "complexity": "low"
        }}
    ]
}}

User task:

{task}
"""


def supervisor_node(state):

    task = state["task"]

    llm = get_llm()

    prompt = SUPERVISOR_PROMPT.format(
        task=task
    )

    response = llm.invoke(prompt)

    content = response.content

    # Some models/providers can return fenced JSON.
    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    content = str(content).strip()

    if content.startswith("```json"):
        content = content[7:]

    if content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        parsed = json.loads(content)
        plan = parsed.get("plan", [])

    except json.JSONDecodeError:
        plan = [
            {
                "id": 1,
                "specialist": "research",
                "description": task,
                "required_inputs": ["user_task"],
                "expected_output": "specialist_response",
                "complexity": "low",
            }
        ]

    if not plan:
        plan = [
            {
                "id": 1,
                "specialist": "research",
                "description": task,
                "required_inputs": ["user_task"],
                "expected_output": "specialist_response",
                "complexity": "low",
            }
        ]

    selected_agent = plan[0]["specialist"]

    return {
    "plan": plan,
    "selected_agent": selected_agent,
    "current_step": 0,
}