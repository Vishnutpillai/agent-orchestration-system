from app.core.llm import get_llm


def data_agent_node(state):

    step = state["current_step"]
    plan_item = state["plan"][step]

    task = plan_item["description"]

    llm = get_llm()

    prompt = f"""
You are the Data Analysis Specialist Agent.

You are executing one subtask from a larger
multi-agent workflow.

Original user task:
{state["task"]}

Your assigned subtask:
{task}

Expected output:
{plan_item.get("expected_output", "Useful data analysis result")}

Provide a focused analysis.

Cover:
- analysis approach
- relevant data concepts
- important considerations
- expected insights

Keep the response below approximately 500 words.

Do not claim that you analyzed an actual dataset
unless a dataset was actually provided.

Do not discuss internal orchestration.
"""
    response = llm.invoke(prompt)

    result = {
        "agent": "data",
        "step": step + 1,
        "task": task,
        "output": response.content,
        "status": "completed",
    }

    return {
        "results": [result],
        "current_step": step + 1,
    }