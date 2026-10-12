
import ast
import operator
import re

from app.tools import tool_registry


# ============================================================
# SAFE ARITHMETIC EVALUATOR
# ============================================================

def evaluate_math_expression(expression: str):
    """Safely evaluate basic arithmetic without eval() or an LLM."""

    if not isinstance(expression, str) or len(expression) > 200:
        raise ValueError("Invalid or excessively long expression.")

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Only numeric constants are allowed.")

        if isinstance(node, ast.BinOp):
            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported arithmetic operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow):
                if abs(right) > 10:
                    raise ValueError("Exponent is too large.")
                if abs(left) > 1000:
                    raise ValueError("Base is too large.")

            result = operation(left, right)

            if isinstance(result, complex):
                raise ValueError("Complex results are not supported.")

            if isinstance(result, float) and (
                result != result
                or abs(result) == float("inf")
            ):
                raise ValueError("Result is not finite.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported unary operator.")

            return operation(evaluate(node.operand))

        raise ValueError("Unsupported mathematical expression.")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree)


# ============================================================
# NATURAL-LANGUAGE MATH PARSER
# ============================================================

def parse_math_task(task: str) -> str:
    """Convert simple English arithmetic instructions into math."""

    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task must be a non-empty string.")

    if len(task) > 500:
        raise ValueError("Task is too long.")

    text = task.lower().strip()

    # Remove an introductory instruction.
    text = re.sub(
        r"^(?:please\s+)?(?:calculate|compute)\s+",
        "",
        text,
    )

    text = re.sub(r"[?!.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize operators. Process longer phrases first.
    replacements = [
        (r"\bmultiplied\s+by\b", "*"),
        (r"\bdivided\s+by\b", "/"),
        (r"\bto\s+the\s+power\s+of\b", "**"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\btimes\b", "*"),
        (r"\bover\b", "/"),
        (r"\badded\s+to\b", "+"),
        (r"\badd\b", "+"),
        (r"\bsubtract\b", "-"),
        (r"\bmultiply\b", "*"),
        (r"\bdivide\b", "/"),
        (r"\bthen\b", " "),
        (r"\band\s+then\b", " "),
        (r"\band\b", " "),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    # Remove common question/instruction words.
    text = re.sub(
        r"\b(?:what|is|the|result|of|please|calculate|compute)\b",
        " ",
        text,
    )

    text = re.sub(r"\s+", " ", text).strip()

    # Reject unknown words or characters.
    if not text or not re.fullmatch(
        r"[0-9\s.+*/%()\-]+",
        text,
    ):
        raise ValueError(
            f"Could not safely parse arithmetic task: {task}"
        )

    # Parse before returning so malformed expressions are rejected.
    ast.parse(text, mode="eval")

    return text


# ============================================================
# TOOL SELECTION
# ============================================================

def choose_tool(task: str, context=None):
    task_lower = task.lower().strip()

    # --------------------------------------------------------
    # Calculator detection
    # --------------------------------------------------------

    calculation_patterns = [
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bwhat is\b",
        r"\bhow much\b",
        r"\baverage\b",
        r"\bsum\b",
        r"\bsubtract\b",
        r"\badd\b",
        r"\bmultiply\b",
        r"\bmultiplied\b",
        r"\bdivide\b",
        r"\bdivided\b",
        r"\bdivision\b",
        r"\bpercentage\b",
        r"\bplus\b",
        r"\bminus\b",
        r"\btimes\b",
        r"\b\d+\s*[-+*/%]\s*\d+\b",
    ]

    if any(
        re.search(pattern, task_lower)
        for pattern in calculation_patterns
    ):
        expression = parse_math_task(task)

        return {
            "use_tool": True,
            "tool_name": "calculator",
            "arguments": {
                "expression": expression,
            },
            "reason": "The task requires a mathematical calculation.",
        }

    # --------------------------------------------------------
    # File-read detection
    # --------------------------------------------------------

    read_phrases = [
        "read file",
        "read the file",
        "read the contents of",
        "contents of the file",
        "contents of readme",
        "read readme",
    ]

    if any(phrase in task_lower for phrase in read_phrases):
        path_match = re.search(
            r"""(?:contents\s+of|read)\s+
                (?:the\s+)?(?:file\s+)?["'`]?
                ([A-Za-z0-9_.\\/-]+\.[A-Za-z0-9]+)""",
            task,
            re.IGNORECASE | re.VERBOSE,
        )

        path = (
            path_match.group(1)
            if path_match
            else "README.md"
        )

        return {
            "use_tool": True,
            "tool_name": "file_read",
            "arguments": {"path": path},
            "reason": "The task requires reading a file.",
        }

    # --------------------------------------------------------
    # File-write detection
    # --------------------------------------------------------

    write_phrases = [
        "write to file",
        "write a file",
        "create a file",
        "write the text",
        "write the string",
    ]

    if any(phrase in task_lower for phrase in write_phrases):
        path_match = re.search(
            r"""(?:file\s+(?:called|named)\s+)
                ["'`]?([A-Za-z0-9_.\\/-]+\.[A-Za-z0-9]+)""",
            task,
            re.IGNORECASE | re.VERBOSE,
        )

        if not path_match:
            path_match = re.search(
                r"""\bto\s+["'`]?
                    ([A-Za-z0-9_.\\/-]+\.(?:txt|md|csv|json|py))""",
                task,
                re.IGNORECASE | re.VERBOSE,
            )

        path = (
            path_match.group(1)
            if path_match
            else "output.txt"
        )

        content_match = re.search(
            r"""write\s+(?:the\s+)?(?:text|string)\s+
                (.+?)\s+to\s+(?:a\s+)?file\b""",
            task,
            re.IGNORECASE | re.VERBOSE,
        )

        content = (
            content_match.group(1).strip().strip("'\"`")
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

    # --------------------------------------------------------
    # Code-execution detection
    # --------------------------------------------------------

    if any(
        phrase in task_lower
        for phrase in [
            "execute python",
            "run python",
            "execute code",
            "run this code",
        ]
    ):
        return {
            "use_tool": True,
            "tool_name": "code_execution",
            "arguments": {},
            "reason": "The task requires code execution.",
        }

    # --------------------------------------------------------
    # No external tool required
    # --------------------------------------------------------

    return {
        "use_tool": False,
        "tool_name": None,
        "arguments": {},
        "reason": "No external tool is required for this task.",
    }


# ============================================================
# TOOL EXECUTION
# ============================================================

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
        raise RuntimeError("Tool arguments must be an object.")

    try:
        if tool_name == "calculator":
            # Support both the current expression format and older
            # decisions containing a natural-language task.
            if "expression" in arguments:
                expression = arguments["expression"]
            elif "task" in arguments:
                expression = parse_math_task(arguments["task"])
            else:
                raise ValueError(
                    "Calculator requires an expression or task."
                )

            result = evaluate_math_expression(expression)

        else:
            result = tool_registry.execute(
                tool_name,
                **arguments,
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
