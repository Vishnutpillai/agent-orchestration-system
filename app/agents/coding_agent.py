import json
import os

from app.core.llm import get_llm
from app.tools.tool_agent import (
    choose_tool,
    execute_tool_decision,
)


def coding_agent_node(state):

    task = state["task"]

    plan = state.get("plan", [])
    results = state.get("results", [])

    # --------------------------------------------------
    # Build previous context
    # --------------------------------------------------

    previous_context = []

    for result in results:

        previous_context.append(
            {
                "agent": result.get(
                    "agent",
                    "",
                ),
                "task": result.get(
                    "task",
                    "",
                ),
                "output": result.get(
                    "output",
                    "",
                )[:2000],
            }
        )

    context_text = json.dumps(
        previous_context,
        ensure_ascii=False,
    )

    # --------------------------------------------------
    # Ask whether a tool is needed
    # --------------------------------------------------

    decision = choose_tool(task)

    print(
        "\n===== CODING TOOL DECISION ====="
    )
    print(decision)
    print(
        "=================================\n"
    )

    # --------------------------------------------------
    # Execute selected tool
    # --------------------------------------------------

    tool_result = execute_tool_decision(
        decision
    )

    print(
        "\n===== TOOL RESULT ====="
    )
    print(tool_result)
    print(
        "=======================\n"
    )

    # --------------------------------------------------
    # Build final coding prompt
    # --------------------------------------------------

    llm = get_llm()

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    prompt = f"""
You are the coding specialist in a
multi-agent AI system.

USER TASK:
{task}

PLAN:
{json.dumps(plan, ensure_ascii=False)}

PREVIOUS AGENT RESULTS:
{context_text}

TOOL DECISION:
{json.dumps(decision, ensure_ascii=False)}

TOOL RESULT:
{json.dumps(tool_result, ensure_ascii=False)}

Create the best Python solution for the user's task.

Requirements:

1. Use the tool result when it is relevant.
2. Do not claim a tool was used if it was not used.
3. If the task is a machine learning pipeline,
   cover the important pipeline stages.
4. Avoid target leakage.
5. Do not invent dataset columns unless provided.
6. Keep the implementation logically executable.
7. Include only the most important code.
8. Explain the approach briefly.
9. Do not mention internal orchestration.
10. Keep the response under approximately 1000 words.
11. Avoid unnecessary comments and explanations.
"""

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise and accurate "
                    "Python coding specialist."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=2200,
    )

    content = response.choices[0].message.content

    finish_reason = (
        response.choices[0].finish_reason
    )

    print(
        f"[CODING] finish_reason={finish_reason}"
    )

    if not content:

        raise RuntimeError(
            "Coding agent returned an empty response."
        )

    return {
        "results": [
            {
                "agent": "coding",
                "task": task,
                "output": content,
                "tool_used": tool_result,
            }
        ]
    }