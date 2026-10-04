from fastapi import FastAPI
from pydantic import BaseModel

from app.core.graph import agent_graph


app = FastAPI(
    title="Agent Orchestration System",
    version="0.1.0",
)


class TaskRequest(BaseModel):
    task: str


@app.get("/")
def root():
    return {
        "message": "Agent Orchestration System API",
        "status": "running",
    }


@app.post("/run")
def run_agent(request: TaskRequest):

    result = agent_graph.invoke(
        {
            "task": request.task,
            "current_step": 0,
            "results": [],
        }
    )

    return {
        "task": request.task,
        "plan": result.get("plan", []),
        "results": result.get("results", []),
        "review": result.get("review", {}),
        "final_response": result.get(
            "final_response",
            "",
        ),
    }