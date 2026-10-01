from app.core.llm import get_llm


def research_agent_node(state):

    step = state["current_step"]
    plan_item = state["plan"][step]

    task = plan_item["description"]

    llm = get_llm()

    prompt = f"""
You are the Research Specialist Agent.

You are executing one subtask from a larger
multi-agent workflow.

Original user task:
{state["task"]}

Your assigned subtask:
{task}

Expected output:
{plan_item.get("expected_output", "Useful research result")}

Provide a focused result.

Use clear sections and concise explanations.
Avoid unnecessary repetition.
Keep the response below approximately 500 words.

Do not discuss the internal orchestration.
"""

    response = llm.invoke(prompt)

    result = {
        "agent": "research",
        "step": step + 1,
        "task": task,
        "output": response.content,
        "status": "completed",
    }

    return {
        "results": [result],
        "current_step": step + 1,
    }