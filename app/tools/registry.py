from typing import Callable, Dict, Any


class ToolRegistry:
    """
    Central registry for all tools available to agents.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable,
    ):
        """
        Register a tool.
        """

        self._tools[name] = {
            "name": name,
            "description": description,
            "function": function,
        }

    def get(self, name: str):
        """
        Get a registered tool by name.
        """

        return self._tools.get(name)

    def list_tools(self):
        """
        Return all registered tools.
        """

        return [
            {
                "name": tool["name"],
                "description": tool["description"],
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        **kwargs,
    ):
        """
        Execute a registered tool.
        """

        tool = self.get(name)

        if not tool:
            raise ValueError(
                f"Tool '{name}' is not registered."
            )

        return tool["function"](**kwargs)


tool_registry = ToolRegistry()