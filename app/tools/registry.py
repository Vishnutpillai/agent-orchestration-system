from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    allowed_agents: List[str]
    rate_limit: Optional[int] = None
    function: Optional[Callable] = None


class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, tool: ToolDefinition):
        self.tools[tool.name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.values())


tool_registry = ToolRegistry()


# Initial Phase 1 tools
tool_registry.register(
    ToolDefinition(
        name="web_search",
        description="Search the web for relevant information.",
        allowed_agents=["research"],
        rate_limit=10,
    )
)

tool_registry.register(
    ToolDefinition(
        name="file_read",
        description="Read a user-provided file.",
        allowed_agents=["research", "data", "coding"],
        rate_limit=20,
    )
)

tool_registry.register(
    ToolDefinition(
        name="file_write",
        description="Write generated content to a file.",
        allowed_agents=["coding"],
        rate_limit=20,
    )
)

tool_registry.register(
    ToolDefinition(
        name="code_execution",
        description="Execute code in a sandboxed environment.",
        allowed_agents=["coding"],
        rate_limit=10,
    )
)

tool_registry.register(
    ToolDefinition(
        name="database_query",
        description="Execute an approved database query.",
        allowed_agents=["data"],
        rate_limit=20,
    )

tool_registry.register(
    ToolDefinition(
        name="api_call",
        description="Call an approved external API.",
        allowed_agents=["research", "data", "coding"],
        rate_limit=10,
    )
)
