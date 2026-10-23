
import json
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langgraph.types import Command
from app.core.graph import agent_graph


DATASET_PATH = PROJECT_ROOT / "evaluation" / "golden_tasks.json"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "evaluation_results.json"

# A new namespace prevents checkpoint IDs from being reused
# across separate evaluation runs.
EVALUATION_RUN_ID = uuid.uuid4().hex


def get_tool_result(state, expected_tool):
    """Find a tool result that actually executed successfully."""

    tool_result = state.get("tool_result") or {}

    if (
        tool_result.get("tool_name") == expected_tool
        and tool_result.get("used") is True
        and not tool_result.get("error")
    ):
        return tool_result

    for item in state.get("results") or []:
        if not isinstance(item, dict):
            continue

        used = item.get("tool_used") or {}

        if (
            used.get("tool_name") == expected_tool
            and used.get("used") is True
            and not used.get("error")
        ):
            return used

    return None


def has_pending_interrupt(state):
    """Return True when a workflow is paused for human approval."""
    return bool(state.get("__interrupt__", []))


def contains_expected_value(expected, state):
    """Check the expected value against the saved workflow state."""

    if expected is None:
        return True

    state_text = json.dumps(
        state,
        ensure_ascii=False,
        default=str,
    ).lower()

    return str(expected).lower() in state_text


def validate_task_result(test_case, state, output_text):
    """Validate a result according to its expected tool and output."""

    checks = {}

    expected = test_case.get("expected_result")
    expected_tool = test_case.get("expected_tool")

    if expected is not None:
        checks["expected_result_present"] = contains_expected_value(
            expected,
            state,
        )

    if expected_tool == "calculator":
        tool_result = get_tool_result(state, "calculator")

        checks["calculator_used"] = tool_result is not None

        if tool_result is not None:
            actual = tool_result.get("result")

            try:
                checks["calculator_result_correct"] = (
                    float(actual) == float(expected)
                )
            except (TypeError, ValueError):
                checks["calculator_result_correct"] = (
                    str(actual) == str(expected)
                )
        else:
            checks["calculator_result_correct"] = False

    elif expected_tool == "file_write":
        expected_file = test_case.get(
            "expected_file",
            "evaluation_test.txt",
        )

        file_path = (PROJECT_ROOT / expected_file).resolve()

        # Prevent a test from checking a file outside the project.
        if PROJECT_ROOT.resolve() not in file_path.parents:
            raise ValueError(
                "Evaluation file path must remain inside the project."
            )

        write_result = get_tool_result(state, "file_write")
        file_exists = file_path.is_file()

        content_matches = False

        if file_exists and expected is not None:
            content_matches = (
                str(expected)
                in file_path.read_text(encoding="utf-8")
            )

        checks["file_write_tool_executed"] = (
            write_result is not None
        )
        checks["file_exists"] = file_exists
        checks["file_content_matches"] = content_matches

    elif expected_tool == "file_read":
        read_result = get_tool_result(state, "file_read")

        read_content = (
            str(read_result.get("result") or "").strip()
            if read_result
            else ""
        )

        checks["file_read_tool_executed"] = (
            read_result is not None
        )
        checks["file_content_returned"] = bool(read_content) and not any(
            marker in read_content.lower()
            for marker in (
                "could not read",
                "not found",
                "error",
            )
        )

        source_file = test_case.get(
            "source_file",
            "README.md",
        )

        checks["source_file_exists"] = (
            PROJECT_ROOT / source_file
        ).is_file()

    else:
        checks["non_empty_output"] = bool(output_text.strip())

    return checks


def run_task(test_case):
    """Run and evaluate a single golden test case."""

    started = time.perf_counter()

    task_id = test_case.get("id", "unknown")
    task = test_case.get("task", "")
    expected_tool = test_case.get("expected_tool")

    result = {
        "id": task_id,
        "category": test_case.get("category", "unknown"),
        "task": task,
        "status": "FAIL",
        "duration_seconds": 0,
        "error": None,
        "output_preview": "",
        "checks": {},
    }

    # Unique thread ID for this test execution.
    thread_id = f"evaluation-{EVALUATION_RUN_ID}-{task_id}"
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 25,
    }

    try:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Test task must not be empty.")

        # Clear only the dedicated evaluation output file.
        if expected_tool == "file_write":
            filename = test_case.get(
                "expected_file",
                "evaluation_test.txt",
            )
            target = (PROJECT_ROOT / filename).resolve()

            if PROJECT_ROOT.resolve() not in target.parents:
                raise ValueError(
                    "Evaluation file must be inside the project."
                )

            if target.is_file():
                target.unlink()

        initial_state = {
            "task": task,
            "current_step": 0,
            "results": [],
        }

        state = agent_graph.invoke(initial_state, config=config)

        if not isinstance(state, dict):
            raise RuntimeError(
                "Workflow returned an invalid state."
            )

        # Only the isolated golden file-write test is automatically
        # approved. Other human-review requests remain paused.
        if (
            test_case.get("auto_approve") is True
            and has_pending_interrupt(state)
        ):
            print(
                "[EVALUATION] Approving isolated test:",
                task_id,
            )

            state = agent_graph.invoke(
                Command(
                    resume={
                        "decision": "approve",
                        "feedback": (
                            "Approved for the isolated evaluation test."
                        ),
                    }
                ),
                config=config,
            )

        if not isinstance(state, dict):
            raise RuntimeError(
                "Resumed workflow returned an invalid state."
            )

        if has_pending_interrupt(state):
            result["status"] = "BLOCKED"
            result["error"] = (
                "Workflow remains paused for human approval."
            )
            return result

        output = (
            state.get("final_response")
            or state.get("response")
            or state.get("output")
            or ""
        )

        output_text = str(output)
        result["output_preview"] = output_text[:1500]

        result["checks"] = validate_task_result(
            test_case,
            state,
            output_text,
        )

        result["status"] = (
            "PASS"
            if result["checks"]
            and all(result["checks"].values())
            else "FAIL"
        )

    except Exception as exc:
        result["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

        # API problems should not be confused with assertion failures.
        error_name = type(exc).__name__.lower()
        error_text = str(exc).lower()

        if any(
            marker in error_name or marker in error_text
            for marker in (
                "timeout",
                "rate limit",
                "ratelimit",
                "429",
                "413",
                "503",
                "connection",
            )
        ):
            result["status"] = "ERROR"

    finally:
        result["duration_seconds"] = round(
            time.perf_counter() - started,
            2,
        )

    return result


def main():
    if not DATASET_PATH.is_file():
        print(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        test_cases = json.load(file)

    if not isinstance(test_cases, list) or not test_cases:
        print("golden_tasks.json must contain a non-empty list.")
        sys.exit(1)

    results = []

    print("=" * 60)
    print("PROJECT 15 - EVALUATION RUNNER")
    print(f"Run ID: {EVALUATION_RUN_ID}")
    print("=" * 60)

    for index, test_case in enumerate(test_cases, start=1):
        print(
            f"\n[{index}/{len(test_cases)}] "
            f"{test_case.get('id', 'unknown')}"
        )
        print(f"Task: {test_case.get('task', '')}")

        item = run_task(test_case)
        results.append(item)

        print(f"Status: {item['status']}")
        print(f"Duration: {item['duration_seconds']} seconds")

        if item["error"]:
            print(f"Error: {item['error']}")

        if item["checks"]:
            print(f"Checks: {item['checks']}")

    total = len(results)
    passed = sum(item["status"] == "PASS" for item in results)
    blocked = sum(item["status"] == "BLOCKED" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)
    failed = sum(item["status"] == "FAIL" for item in results)

    report = {
        "project": "Project 15 - Agent Orchestration System",
        "run_id": EVALUATION_RUN_ID,
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "errors": errors,
        "success_rate_percent": round(
            passed / total * 100,
            2,
        ),
        "results": results,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RESULTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")
    print(f"Blocked     : {blocked}")
    print(f"Errors      : {errors}")
    print(f"Success rate: {report['success_rate_percent']}%")
    print(f"Report saved: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
