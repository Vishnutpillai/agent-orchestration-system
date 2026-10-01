from app.core.llm import get_llm


def coding_agent_node(state):

    step = state["current_step"]
    plan_item = state["plan"][step]

    task = plan_item["description"]

    llm = get_llm()
    prompt = f"""
You are the Coding Specialist Agent.

You are executing one subtask from a larger
multi-agent workflow.

Original user task:
{state["task"]}

Your assigned subtask:
{task}

Expected output:
{plan_item.get("expected_output", "Working code and explanation")}

Provide:
- explanation
- implementation
- important considerations
- possible edge cases

Use Python unless another language is explicitly requested.

IMPORTANT CODE RULES:

1. Generate syntactically valid Python.
2. The code must run as a normal .py Python script.
3. Do NOT use Jupyter-only syntax such as:
   - %matplotlib inline
   - %%time
   - display()
4. Use print() instead of display().
5. Do not put extra quotation marks inside Python expressions.
6. Make sure all parentheses, brackets and quotation marks are balanced.
7. If you provide a code block, use:
   ```python
   """
   
    response = llm.invoke(prompt)

    result = {
        "agent": "coding",
        "step": step + 1,
        "task": task,
        "output": response.content,
        "status": "completed",
    }

    return {
        "results": [result],
        "current_step": step + 1,
    }