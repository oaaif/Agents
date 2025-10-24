from __future__ import annotations
import os
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel
from app.server_multi import create_agent_subapp
from agents.mcp_adapter import MCPBackend
from agents.python_adapter import PythonFunctionBackend

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

# Define your agents here (or load from YAML/ENV)
REGISTRY: Dict[str, object] = {
    "mcp-tools": MCPBackend(
        command="uv", args=["run", "server", "fastmcp_quickstart", "stdio"], name="MCP Tools Agent"
    ),
    "echo": PythonFunctionBackend(lambda s, meta=None: f"Echo[{meta.get('task_id','?')}]: {s}", name="Echo Agent"),
}

app = FastAPI(title="A2A Hub", version="1.0.0")

class AgentIndexItem(BaseModel):
    id: str
    name: str
    card_url: str
    rpc_url: str

@app.get("/agents", response_model=list[AgentIndexItem])
async def list_agents():
    out = []
    for agent_id, backend in REGISTRY.items():
        mount_prefix = f"/agents/{agent_id}"
        # Minimal name without constructing whole card: use describe()
        desc = backend.describe()
        out.append(AgentIndexItem(
            id=agent_id,
            name=desc.name,
            card_url=f"{PUBLIC_BASE_URL}{mount_prefix}/.well-known/agent-card.json",
            rpc_url=f"{PUBLIC_BASE_URL}{mount_prefix}/",
        ))
    return out

# Mount one sub‑app per agent
for agent_id, backend in REGISTRY.items():
    mount_prefix = f"/agents/{agent_id}"
    sub = create_agent_subapp(PUBLIC_BASE_URL, mount_prefix, backend)
    app.mount(mount_prefix, sub)