
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.types import Command

from app.core.graph import agent_graph
from app.tools import tool_registry
from app.observability.logging_config import configure_logging


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

configure_logging()
logger = logging.getLogger("agent15")


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Agent Orchestration System",
    version="0.2.0",
)


# =========================================================
# REQUEST MODELS
# =========================================================

class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10000)


class ApprovalRequest(BaseModel):
    decision: str
    feedback: str = Field(default="", max_length=2000)


# =========================================================
# WORKFLOW CONFIGURATION
# =========================================================

def workflow_config(thread_id: str) -> dict:
    """Build the checkpoint configuration for a workflow."""
    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 25,
    }


# =========================================================
# RESPONSE FORMATTING
# =========================================================

def workflow_response(
    result: dict,
    thread_id: str,
    requested_task: str = "",
) -> dict:
    """Return either a pending approval or a completed result."""

    interrupts = result.get("__interrupt__", ())

    if interrupts:
        interrupt_value = getattr(interrupts[0], "value", {})

        return {
            "status": "approval_required",
            "thread_id": thread_id,
            "approval_request": interrupt_value,
            "task": result.get("task", requested_task),
            "plan": result.get("plan", []),
            "results": result.get("results", []),
        }

    return {
        "status": "completed",
        "thread_id": thread_id,
        "task": result.get("task", requested_task),
        "plan": result.get("plan", []),
        "results": result.get("results", []),
        "review": result.get("review", {}),
        "final_response": result.get("final_response", ""),
    }


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():
    """Return basic API status."""

    logger.info(
        "Health check requested",
        extra={
            "event": "health_check",
            "status": "running",
        },
    )

    return {
        "message": "Agent Orchestration System API",
        "status": "running",
    }


# =========================================================
# DEDICATED HEALTH ENDPOINT
# =========================================================

@app.get("/health")
def health_check():
    """Basic liveness check for deployment platforms."""

    return {
        "status": "healthy",
        "service": "agent-orchestration-system",
        "version": app.version,
    }


# =========================================================
# RUN A NEW TASK
# =========================================================

@app.post("/run")
def run_agent(request: TaskRequest):
    task = request.task.strip()

    if not task:
        raise HTTPException(
            status_code=422,
            detail="Task must not be empty or whitespace only.",
        )

    thread_id = str(uuid.uuid4())
    config = workflow_config(thread_id)
    started_at = time.perf_counter()

    logger.info(
        "Workflow started",
        extra={
            "event": "workflow_started",
            "thread_id": thread_id,
            "status": "started",
        },
    )

    try:
        result = agent_graph.invoke(
            {
                "task": task,
                "current_step": 0,
                "results": [],
            },
            config=config,
        )

        if not isinstance(result, dict):
            raise RuntimeError(
                "Workflow returned an invalid result."
            )

        response = workflow_response(
            result,
            thread_id,
            task,
        )

        logger.info(
            "Workflow finished",
            extra={
                "event": "workflow_finished",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": response["status"],
            },
        )

        return response

    except Exception:
        logger.exception(
            "Agent workflow failed",
            extra={
                "event": "workflow_failed",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": "failed",
            },
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "The agent workflow could not complete this task. "
                "Please try again later."
            ),
        ) from None


# =========================================================
# APPROVE OR REJECT A PAUSED TASK
# =========================================================

@app.post("/approvals/{thread_id}")
def decide_approval(
    thread_id: str,
    request: ApprovalRequest,
):
    decision = request.decision.strip().lower()

    if decision not in {"approve", "reject"}:
        raise HTTPException(
            status_code=422,
            detail="Decision must be 'approve' or 'reject'.",
        )

    config = workflow_config(thread_id)
    started_at = time.perf_counter()

    logger.info(
        "Approval decision received",
        extra={
            "event": "approval_decision_received",
            "thread_id": thread_id,
            "status": decision,
        },
    )

    try:
        # Find the saved workflow checkpoint.
        snapshot = agent_graph.get_state(config)

        if not snapshot.config or not snapshot.next:
            raise HTTPException(
                status_code=404,
                detail="No pending workflow was found for this thread.",
            )

        if "human_review" not in snapshot.next:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This workflow is not waiting for human approval."
                ),
            )

        # Resume the same workflow with the explicit decision.
        result = agent_graph.invoke(
            Command(
                resume={
                    "decision": decision,
                    "feedback": request.feedback,
                }
            ),
            config=config,
        )

        if not isinstance(result, dict):
            raise RuntimeError(
                "Workflow returned an invalid result."
            )

        response = workflow_response(
            result,
            thread_id,
            result.get("task", ""),
        )

        logger.info(
            "Approval workflow finished",
            extra={
                "event": "approval_workflow_finished",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": response["status"],
            },
        )

        return response

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Approval workflow failed",
            extra={
                "event": "approval_workflow_failed",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": "failed",
            },
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "The workflow could not resume. "
                "Check the server logs."
            ),
        ) from None


# =========================================================
# WORKFLOW STATUS
# =========================================================

@app.get("/runs/{thread_id}")
def get_run_status(thread_id: str):
    """Inspect a saved workflow without starting or resuming it."""

    started_at = time.perf_counter()
    config = workflow_config(thread_id)

    try:
        snapshot = agent_graph.get_state(config)

        # An unknown thread has no saved state.
        if (
            snapshot.metadata is None
            and not snapshot.values
            and not snapshot.next
        ):
            raise HTTPException(
                status_code=404,
                detail="No workflow was found for this thread.",
            )

        state = snapshot.values or {}
        next_nodes = list(snapshot.next or [])

        if "human_review" in next_nodes:
            status = "approval_required"
        elif not next_nodes:
            status = "completed"
        else:
            status = "in_progress"

        response = {
            "thread_id": thread_id,
            "status": status,
            "task": state.get("task", ""),
            "current_step": state.get("current_step", 0),
            "plan": state.get("plan", []),
            "results": state.get("results", []),
            "next_nodes": next_nodes,
        }

        # Include the approval request when the workflow is paused.
        if status == "approval_required":
            approval_request = None

            for task_snapshot in snapshot.tasks:
                for interrupt_item in task_snapshot.interrupts:
                    approval_request = interrupt_item.value
                    break

                if approval_request is not None:
                    break

            response["approval_request"] = approval_request

        logger.info(
            "Workflow status retrieved",
            extra={
                "event": "workflow_status_retrieved",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": status,
            },
        )

        return response

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Could not retrieve workflow status",
            extra={
                "event": "workflow_status_failed",
                "thread_id": thread_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                "status": "failed",
            },
        )

        raise HTTPException(
            status_code=503,
            detail="Workflow status could not be retrieved.",
        ) from None


# =========================================================
# AVAILABLE TOOLS
# =========================================================

@app.get("/tools")
def list_tools():
    """List tools registered with the agent system."""

    logger.info(
        "Tool registry requested",
        extra={
            "event": "tools_listed",
            "status": "success",
        },
    )

    return {
        "tools": tool_registry.list_tools(),
    }
