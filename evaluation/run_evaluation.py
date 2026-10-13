

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.graph import agent_graph

DATASET_PATH = PROJECT_ROOT / "evaluation" / "golden_tasks.json"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "evaluation_results.json"



def get_tool_result(state, expected_tool):
    """Find a successfully executed tool result in the graph state."""
    tool_result = state.get("tool_result") or {}

    if (
        tool_result.get("tool_name") == expected_tool
        and tool_result.get("used") is True
    ):
        return tool_result

    results_list = state.get("results") or []

    for item in results_list:
        if not isinstance(item, dict):
            continue

        used = item.get("tool_used") or {}

        if (
            used.get("tool_name") == expected_tool
            and used.get("used") is True
        ):
            return used

    return None


def run_task(test_case):
    """Run a task and verify its actual result."""
    started = time.perf_counter()

    task_id = test_case.get("id", "unknown")
    category = test_case.get("category", "unknown")
    task = test_case.get("task", "")
    expected = test_case.get("expected_result")
    expected_tool = test_case.get("expected_tool")

    result = {
        "id": task_id,
        "category": category,
        "task": task,
        "status": "FAIL",
        "duration_seconds": 0,
        "error": None,
        "output_preview": "",
        "checks": {},
    }

    try:
        # Clean up the old file BEFORE the agent executes.
        # This prevents a previous run from making the test pass.
        if expected_tool == "file_write":
            test_file = PROJECT_ROOT / "evaluation_test.txt"
            if test_file.is_file():
                test_file.unlink()

        state = agent_graph.invoke({"task": task})

        output = (
            state.get("final_response")
            or state.get("response")
            or state.get("output")
            or ""
        )
        output_text = str(output)
        state_text = json.dumps(state, ensure_ascii=False, default=str)

        result["output_preview"] = output_text[:1500]

        # Check expected result in the graph state.
        if expected is not None:
            result["checks"]["expected_result_present"] = (
                str(expected).lower() in state_text.lower()
            )

        # Verify calculator execution and result.
        if expected_tool == "calculator":
            tool_result = get_tool_result(state, "calculator")

            result["checks"]["calculator_used"] = (
                tool_result is not None
                and not tool_result.get("error")
            )

            result["checks"]["calculator_result_present"] = (
                expected is not None
                and str(expected) in state_text
            )

        # Verify real file creation and content.
        if expected_tool == "file_write":
            file_path = PROJECT_ROOT / "evaluation_test.txt"
            write_result = get_tool_result(state, "file_write")

            file_exists = file_path.is_file()
            content_matches = False

            if file_exists:
                content = file_path.read_text(encoding="utf-8")
                content_matches = (
                    expected is not None and expected in content
                )

            result["checks"]["file_write_tool_executed"] = (
                write_result is not None
                and not write_result.get("error")
            )
            result["checks"]["file_exists"] = file_exists
            result["checks"]["file_content_matches"] = content_matches

        # Verify that file_read returned actual contents.
        if expected_tool == "file_read":
            read_result = get_tool_result(state, "file_read")
            read_content = (
                str(read_result.get("result") or "")
                if read_result
                else ""
            ).strip()

            read_content_valid = bool(read_content) and not any(
                marker in read_content.lower()
                for marker in (
                    "could not read",
                    "not found",
                    "error",
                )
            )

            result["checks"]["file_read_tool_executed"] = (
                read_result is not None
                and not read_result.get("error")
            )
            result["checks"]["file_content_returned"] = (
                read_content_valid
            )
            result["checks"]["source_file_exists"] = (
                PROJECT_ROOT / "README.md"
            ).is_file()

        # Research and coding tasks should produce a non-empty answer.
        if not result["checks"]:
            result["checks"]["non_empty_output"] = bool(
                output_text.strip()
            )

        result["status"] = (
            "PASS"
            if result["checks"]
            and all(result["checks"].values())
            else "FAIL"
        )

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    result["duration_seconds"] = round(
        time.perf_counter() - started, 2
    )
    return result


def main():
    if not DATASET_PATH.is_file():
        print(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        test_cases = json.load(file)

    if not isinstance(test_cases, list) or not test_cases:
        print("Error: golden_tasks.json must contain a non-empty JSON list.")
        sys.exit(1)

    results = []

    print("=" * 60)
    print("PROJECT 15 - EVALUATION RUNNER")
    print("=" * 60)

    for index, test_case in enumerate(test_cases, start=1):
        print(
            f"\n[{index}/{len(test_cases)}] "
            f"{test_case.get('id', 'unknown')}"
        )
        print(f"Task: {test_case.get('task', '')}")

        result = run_task(test_case)
        results.append(result)

        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration_seconds']} seconds")

        if result["error"]:
            print(f"Error: {result['error']}")

        if result["checks"]:
            print(f"Checks: {result['checks']}")

    total = len(results)
    passed = sum(
        item["status"] == "PASS" for item in results
    )
    failed = total - passed
    success_rate = round(passed / total * 100, 2)

    report = {
        "project": "Project 15 - Agent Orchestration System",
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "success_rate_percent": success_rate,
        "results": results,
    }

    with RESULTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")
    print(f"Success rate: {success_rate}%")
    print(f"Report saved: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
