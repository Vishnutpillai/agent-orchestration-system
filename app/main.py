
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.graph import agent_graph
from app.tools import tool_registry


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Orchestration System",
    version="0.1.0",
)


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10000)


@app.get("/")
def root():
    return {
        "message": "Agent Orchestration System API",
        "status": "running",
    }


@app.post("/run")
def run_agent(request: TaskRequest):
    task = request.task.strip()

    if not task:
        raise HTTPException(
            status_code=422,
            detail="Task must not be empty or whitespace only.",
        )

    try:
        result = agent_graph.invoke(
            {
                "task": task,
                "current_step": 0,
                "results": [],
            },
            config={"recursion_limit": 25},
        )

        if not isinstance(result, dict):
            raise RuntimeError("Workflow returned an invalid result.")

        return {
            "task": task,
            "plan": result.get("plan", []),
            "results": result.get("results", []),
            "review": result.get("review", {}),
            "final_response": result.get("final_response", ""),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Agent workflow failed.")

        raise HTTPException(
            status_code=503,
            detail=(
                "The agent workflow could not complete this task. "
                "Please try again later."
            ),
        ) from None


@app.get("/tools")
def list_tools():
    return {
        "tools": tool_registry.list_tools()
    }
