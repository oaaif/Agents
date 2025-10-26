from fastapi import FastAPI
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.utils.message import new_agent_text_message
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentInterface


# ---- Executors ----
class UppercaseExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input() or ""
        await event_queue.enqueue_event(
            new_agent_text_message(text.upper(), context_id=context.context_id, task_id=context.task_id)
        )


class WordCountExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input() or ""
        count = len(text.split()) if text else 0
        await event_queue.enqueue_event(
            new_agent_text_message(str(count), context_id=context.context_id, task_id=context.task_id)
        )


# ---- Factory to build A2A worker sub-apps ----
def _build_worker_app(name: str, description: str, base_path_hint: str, executor: AgentExecutor) -> FastAPI:
    agent_card = AgentCard(
        name=name,
        description=description,
        url=base_path_hint,
        version="0.1.0",
        protocol_version="1.0",
        skills=[AgentSkill(id="process_text", name="process_text", description="Process a single text input.")],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        additional_interfaces=[AgentInterface(transport="rest", url=base_path_hint)],
    )
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        queue_manager=InMemoryQueueManager(),
    )
    return A2ARESTFastAPIApplication(agent_card=agent_card, http_handler=handler).build(
        agent_card_url='/.well-known/agent-card.json',
        rpc_url=''
    )


def create_uppercase_app() -> FastAPI:
    return _build_worker_app(
        name="Uppercase Worker",
        description="Converts text to UPPERCASE.",
        base_path_hint="/agents/uppercase",
        executor=UppercaseExecutor(),
    )


def create_wordcount_app() -> FastAPI:
    return _build_worker_app(
        name="WordCount Worker",
        description="Counts words in text.",
        base_path_hint="/agents/wordcount",
        executor=WordCountExecutor(),
    )