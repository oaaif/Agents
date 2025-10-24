from __future__ import annotations
import asyncio, uuid
from typing import Any
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import Message
from agents.base import AbstractBackend

class BaseAgentExecutor(AgentExecutor):
    def __init__(self, backend: AbstractBackend):
        self.backend = backend

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        prompt = context.get_user_input(delimiter="\n") or ""
        meta = {"task_id": context.task_id, "context_id": context.context_id}
        await event_queue.enqueue_event(_text_message(context.task_id, "Agent started..."))
        try:
            result = await self.backend.run(prompt, meta)
            await event_queue.enqueue_event(_text_message(context.task_id, result.get("text") or ""))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await event_queue.enqueue_event(_text_message(context.task_id, f"Error: {e}"))
        finally:
            await event_queue.close()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(_text_message(context.task_id, "Cancellation requested."))
        await event_queue.close(immediate=True)

def _text_message(task_id: str | None, text: str) -> Message:
    return Message.model_validate({
        "taskId": task_id or f"task_{uuid.uuid4().hex[:8]}",
        "messageId": f"msg_{uuid.uuid4().hex[:8]}",
        "role": "assistant",
        "parts": [{"kind": "text", "text": text}],
    })