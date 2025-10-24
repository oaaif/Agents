from __future__ import annotations
from typing import Any, Callable, Dict
from .base import AbstractBackend, AgentDescriptor, SkillSpec

class PythonFunctionBackend(AbstractBackend):
    def __init__(self, fn: Callable, name: str = "Python Echo Agent", streaming: bool = False):
        self.fn = fn
        self._name = name
        self._streaming = streaming

    def describe(self) -> AgentDescriptor:
        return AgentDescriptor(
            name=self._name,
            description="Wraps a Python function for simple prompt→text responses.",
            streaming=self._streaming,
            skills=[
                SkillSpec(
                    id="general.echo",
                    name="Echo",
                    description="Echoes user input; demo of non-MCP backend.",
                    input_modes=["text"],
                    output_modes=["text"],
                    tags=["echo"],
                )
            ],
        )

    async def run(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        if getattr(self.fn, "__code__", None) and self.fn.__code__.co_argcount >= 2:
            out = self.fn(prompt, meta)
        else:
            out = self.fn(prompt)
        return {"text": str(out)}