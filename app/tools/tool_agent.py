import json
import re

from app.core.llm import get_llm
from app.tools import tool_registry


def choose_tool(task: str, context=None):

    task_lower = task.lower().strip()

    # --------------------------------------------------
    # Calculator detection
    # --------------------------------------------------

    calculation_patterns = [
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\baverage\b",
        r"\bsum\b",
        r"\bsubtract\b",
        r"\badd\b",
        r"\bmultiply\b",
        r"\bmultiplied\b",
        r"\bdivide\b",
        r"\bdivided\b",
        r"\bpercentage\b",
    ]

    if any(
        re.search(pattern, task_lower)
        for pattern in calculation_patterns
    ):
        llm = get_llm()

        prompt = f"""
Convert the following mathematical task into a calculator expression.

TASK:
{task}

Return exactly this JSON structure:

{{
  "use_tool": true,
  "tool_name": "calculator",
  "arguments": {{
    "expression": "2+2"
  }},
  "reason": "The task requires a mathematical calculation."
}}

Return ONLY JSON.
"""

        response = llm.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Convert math instructions into calculator expressions."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        choice = response.choices[0]

        print(
            f"[TOOL AGENT] finish_reason={choice.finish_reason}"
        )

        content = choice.message.content

        if not content:
            raise RuntimeError(
                "Tool selector returned an empty response."
            )

        print("\n===== TOOL AGENT RESPONSE =====")
        print(content)
        print("===============================\n")

        return json.loads(content)

    # --------------------------------------------------
    # File read detection
    # --------------------------------------------------

    if (
        "read file" in task_lower
        or "read the file" in task_lower
        or "contents of the file" in task_lower
    ):
        return {
            "use_tool": True,
            "tool_name": "file_read",
            "arguments": {},
            "reason": "The task requires reading a file.",
        }

    # --------------------------------------------------
    # File write detection
    # --------------------------------------------------

    if (
        "write to file" in task_lower
        or "write a file" in task_lower
        or "create a file" in task_lower
        or "write the text" in task_lower
    ):
        path_match = re.search(
            r"(?:file called|file named|to)\s+[`'\"]?([A-Za-z0-9_.\\/-]+)[`'\"]?",
            task,
            re.IGNORECASE,
        )

        content_match = re.search(
            r"write (?:the text|string)\s+(.+?)\s+to (?:a )?file",
            task,
            re.IGNORECASE,
        )

        path = (
            path_match.group(1)
            if path_match
            else "output.txt"
        )

        content = (
            content_match.group(1).strip(" '\"")
            if content_match
            else "Hello Agent 15"
        )

        return {
            "use_tool": True,
            "tool_name": "file_write",
            "arguments": {
                "path": path,
                "content": content,
            },
            "reason": "The task requires writing a file.",
        }

    # --------------------------------------------------
    # Code execution detection
    # --------------------------------------------------

    if (
        "execute python" in task_lower
        or "run python" in task_lower
        or "execute code" in task_lower
        or "run this code" in task_lower
    ):
        return {
            "use_tool": True,
            "tool_name": "code_execution",
            "arguments": {},
            "reason": "The task requires code execution.",
        }

    # --------------------------------------------------
    # No external tool
    # --------------------------------------------------

    return {
        "use_tool": False,
        "tool_name": None,
        "arguments": {},
        "reason": "No external tool is required for this task.",
    }


def execute_tool_decision(decision: dict):

    if not decision.get("use_tool", False):
        return {
            "used": False,
            "tool_name": None,
            "result": None,
        }

    tool_name = decision.get("tool_name")
    arguments = decision.get("arguments", {})

    if not tool_name:
        raise RuntimeError(
            "Tool execution requested but tool_name is missing."
        )

    if not isinstance(arguments, dict):
        raise RuntimeError(
            "Tool arguments must be an object."
        )

    try:

        result = tool_registry.execute(
            tool_name,
            **arguments
        )

        return {
            "used": True,
            "tool_name": tool_name,
            "result": result,
        }

    except Exception as exc:

        return {
            "used": True,
            "tool_name": tool_name,
            "result": None,
            "error": str(exc),
        }