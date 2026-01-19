import json
from typing import Any, Dict

class SimpleHelloTool:
    def __init__(self):
        self.name = "simple_hello" # Renamed to avoid collision
        self.description = "Says hello to the given name or a generic hello if no name is provided."
        self.inputs = {
            "name": {"type": "string", "description": "The name to say hello to (optional).", "nullable": True}
        }

    def forward(self, **kwargs: Any) -> str:
        name = kwargs.get("name")
        if name:
            message = f"Hello, {name}!"
        else:
            message = "Hello there!"
        return json.dumps({"result": message, "status": "success"})

# This is a factory function for the tool, used by the tool registry
def get_tool():
    return SimpleHelloTool()