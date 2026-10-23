
import os

import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "AGENT15_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

REQUEST_TIMEOUT = 180


st.set_page_config(
    page_title="Project 15 | Agent Orchestration",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Project 15")
st.subheader("Agent Orchestration System")
st.caption(
    "Coordinate AI specialists, execute tools with human approval, "
    "and monitor workflow results."
)


def api_request(method, path, **kwargs):
    """Make a request to the FastAPI backend."""
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(
            method,
            url,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )

        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text}

        if not response.ok:
            detail = data.get("detail", data)
            st.error(f"API error ({response.status_code}): {detail}")
            return None

        return data

    except requests.RequestException as exc:
        st.error(
            "Cannot connect to the FastAPI backend. "
            "Check that the API server is running."
        )
        st.caption(str(exc))
        return None


def show_results(data):
    """Display workflow plans, results, and final responses."""

    if data.get("plan"):
        st.markdown("### Workflow plan")
        st.json(data["plan"])

    if data.get("results"):
        st.markdown("### Specialist and tool results")

        for index, item in enumerate(data["results"], start=1):
            title = (
                f"{index}. {item.get('agent', 'Agent')} "
                f"— {item.get('status', 'unknown')}"
            )

            with st.expander(title):
                st.write("Task:", item.get("task", ""))
                st.write("Output:", item.get("output", ""))

                if item.get("tool_used"):
                    st.json(item["tool_used"])

    if data.get("review"):
        st.markdown("### Reviewer feedback")
        st.json(data["review"])

    if data.get("final_response"):
        st.markdown("### Final response")
        st.markdown(str(data["final_response"]))


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.header("System status")

    if st.button("Check API health", use_container_width=True):
        health = api_request("GET", "/")
        if health:
            st.success(health.get("status", "API responded"))
            st.json(health)

    st.caption(f"Backend: {API_BASE_URL}")

    st.divider()

    if st.button("List available tools", use_container_width=True):
        tools = api_request("GET", "/tools")
        if tools is not None:
            st.session_state["available_tools"] = tools

    if "available_tools" in st.session_state:
        st.json(st.session_state["available_tools"])


# ---------------------------------------------------------
# TASK SUBMISSION
# ---------------------------------------------------------

st.markdown("## Submit a task")

task = st.text_area(
    "What would you like the AI agents to do?",
    placeholder=(
        "Examples:\n"
        "Calculate 50 multiplied by 3 and then add 20.\n"
        "Explain how machine learning works.\n"
        "Read the contents of README.md.\n"
        "Write the text Hello Project 15 to evaluation_test.txt."
    ),
    height=130,
    max_chars=10000,
)

if st.button("Run workflow", type="primary", use_container_width=True):
    if not task.strip():
        st.warning("Please enter a task first.")
    else:
        with st.spinner("Running the agent workflow..."):
            response = api_request(
                "POST",
                "/run",
                json={"task": task.strip()},
            )

        if response is not None:
            st.session_state["last_workflow"] = response
            st.session_state["last_thread_id"] = response.get(
                "thread_id", ""
            )

# ---------------------------------------------------------
# WORKFLOW RESULT
# ---------------------------------------------------------

workflow = st.session_state.get("last_workflow")

if workflow:
    st.divider()
    st.markdown("## Workflow details")

    status = workflow.get("status", "unknown")
    thread_id = workflow.get("thread_id", "")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Status", status.replace("_", " ").title())

    with col2:
        st.text("Thread ID")
        st.code(thread_id or "Not available")

    if status == "approval_required":
        st.warning("Human approval is required before proceeding.")

        approval = workflow.get("approval_request", {})
        if approval:
            st.markdown("### Requested action")
            st.json(approval)

        feedback = st.text_area(
            "Approval feedback (optional)",
            key="approval_feedback",
            max_chars=2000,
        )

        col_approve, col_reject = st.columns(2)

        with col_approve:
            if st.button(
                "Approve action",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Resuming approved workflow..."):
                    response = api_request(
                        "POST",
                        f"/approvals/{thread_id}",
                        json={
                            "decision": "approve",
                            "feedback": feedback,
                        },
                    )

                if response is not None:
                    st.session_state["last_workflow"] = response
                    st.rerun()

        with col_reject:
            if st.button(
                "Reject action",
                use_container_width=True,
            ):
                with st.spinner("Recording rejection..."):
                    response = api_request(
                        "POST",
                        f"/approvals/{thread_id}",
                        json={
                            "decision": "reject",
                            "feedback": feedback,
                        },
                    )

                if response is not None:
                    st.session_state["last_workflow"] = response
                    st.rerun()

    elif status == "completed":
        st.success("Workflow completed.")
        show_results(workflow)

    else:
        st.info(f"Workflow status: {status}")

    if thread_id:
        with st.expander("Refresh saved workflow status"):
            if st.button("Refresh status"):
                latest = api_request(
                    "GET",
                    f"/runs/{thread_id}",
                )

                if latest is not None:
                    st.json(latest)

                    latest_status = latest.get("status")

                    if latest_status == "approval_required":
                        st.session_state["last_workflow"] = {
                            **workflow,
                            **latest,
                        }
                        st.rerun()

st.divider()
st.caption("Project 15 · FastAPI · LangGraph · Streamlit")
