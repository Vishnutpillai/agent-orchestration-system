from app.core.llm import get_llm
import os

def data_agent_node(state):

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    task = plan[current_step]["description"]

    llm = get_llm()

    prompt = f"""
You are the data specialist in a multi-agent AI system.

Complete the following task:

{task}

Requirements:
- Explain the required data-analysis steps briefly.
- Use 4-6 bullet points.
- Avoid unnecessary detail.
- Finish the response completely.
"""

    response = llm.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=[
            {
                "role": "system",
                "content": "You are a data analysis specialist.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=350,
    )
    print(f"[DATA] finish_reason={response.choices[0].finish_reason}")

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError(
            "Data agent received an empty response from Groq."
        )

    result = {
        "agent": "data",
        "task": task,
        "output": output,
        "status": "completed",
    }

    return {
        "results": [result],
        "current_step": current_step + 1,
    }
