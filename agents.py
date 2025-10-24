from __future__ import annotations
import os
from typing import Dict, List
from fastapi import FastAPI
from pydantic import BaseModel

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.agent_execution.simple_request_context_builder import SimpleRequestContextBuilder
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager

# Optional Redis (recommended for scale)
REDIS_URL = os.getenv("REDIS_URL")
USE_REDIS = bool(REDIS_URL)
if USE_REDIS:
    from a2a_redis import RedisTaskStore, RedisStreamsQueueManager, RedisPushNotificationConfigStore
    import redis.asyncio as redis
    _redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

from app.agent_card import build_agent_card
from agents.base import AbstractBackend
from agents.mcp_adapter import MCPBackend
from agents.python_adapter import PythonFunctionBackend
from agents.base import AgentDescriptor
from agents.base import AbstractBackend
from agents.base import AgentDescriptor

# --- Registry types ---
class AgentSpec(BaseModel):
    id: str
    backend: AbstractBackend

def _make_stores(prefix: str):
    if USE_REDIS:
        task_store = RedisTaskStore(_redis, prefix=f"{prefix}:tasks:")
        queue_manager = RedisStreamsQueueManager(_redis, prefix=f"{prefix}:queues:")
        push_store = RedisPushNotificationConfigStore(_redis, prefix=f"{prefix}:push:")
    else:
        task_store = InMemoryTaskStore()
        queue_manager = InMemoryQueueManager()
        push_store = None
    return task_store, queue_manager, push_store

def create_agent_subapp(base_url: str, mount_prefix: str, backend: AbstractBackend) -> FastAPI:
    from agents.base import AgentDescriptor  # for type
    from agents.base import AbstractBackend
    from agents.base import AgentDescriptor
    from agents.base import AbstractBackend

    desc: AgentDescriptor = backend.describe()
    agent_card = build_agent_card(base_url, mount_prefix, desc)

    # Namespaced infra per agent
    ns = ("a2a" + mount_prefix.replace("/", ":")).strip(":")
    task_store, queue_manager, push_store = _make_stores(ns)

    from a2a.server.agent_execution.agent_executor import AgentExecutor
    from agents.base_executor import BaseAgentExecutor  # see below, or reuse yours
    executor = BaseAgentExecutor(backend)

    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        queue_manager=queue_manager,
        push_config_store=push_store,
        request_context_builder=SimpleRequestContextBuilder(
            should_populate_referred_tasks=True, task_store=task_store
        ),
    )

    # Build sub‑app; card and RPC live under the mount prefix
    sub = A2AFastAPIApplication(agent_card=agent_card, http_handler=handler).build(
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/",  # POST JSON-RPC and SSE stream relative to the mount
        extended_agent_card_url="/agent/authenticatedExtendedCard",
        title=f"{desc.name}",
        version=desc.version,
        docs_url="/docs",
    )
    return sub

# If you put BaseAgentExecutor in agents/base_executor.py
# Otherwise import from where you defined it previously
# agents/base_executor.py
# (Provide this file if you don’t already have the BaseAgentExecutor.)