from __future__ import annotations
import json
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .base import AbstractBackend, AgentDescriptor, SkillSpec

class MCPBackend(AbstractBackend):
    def __init__(self, command: str, args: List[str] | None = None, env: Dict[str, str] | None = None, name: str = "MCP Agent"):
        self._stdio_params = StdioServerParameters(command=command, args=args or [], env=env or {})
        self._name = name

    def describe(self) -> AgentDescriptor:
        return AgentDescriptor(
            name=self._name,
            description="Agent backed by a Model Context Protocol server over stdio.",
            streaming=True,
            skills=[
                SkillSpec(
                    id="mcp.chat",
                    name="MCP Chat",
                    description="Routes user input to an MCP tool (default: chat).",
                    input_modes=["text", "json"],
                    output_modes=["text"],
                    tags=["mcp", "tools"],
                )
            ],
        )

    async def run(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        try:
            j = json.loads(prompt)
            tool_name = j.get("tool")
            arguments = j.get("arguments", {})
        except Exception:
            tool_name = "chat"
            arguments = {"input": prompt}

        async with stdio_client(self._stdio_params) as (read, write):
            async with ClientSession(read, write) as session:
                _ = await session.list_tools()
                items = await session.call_tool(tool_name, arguments)
                texts = []
                for item in items:
                    text = getattr(item, "text", None) or str(item)
                    texts.append(text)
                return {"text": "\n".join(texts), "metadata": {"tool": tool_name}}