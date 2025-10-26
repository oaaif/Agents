# agents/rag_backend.py
from .base import AbstractBackend, AgentDescriptor, SkillSpec
class RAGBackend(AbstractBackend):
    def __init__(self, retriever, llm): self.retriever, self.llm = retriever, llm
    def describe(self) -> AgentDescriptor:
        return AgentDescriptor(
            name="RAG QA Agent",
            description="Retrieval-augmented QA; supports citations JSON.",
            streaming=True,
            skills=[SkillSpec(
                id="qa.retrieve", name="RAG QA",
                description="Answer questions with sources.",
                input_modes=["text"], output_modes=["text","json"], tags=["rag","qa","citations"]
            )]
        )
    async def run(self, prompt: str, meta: dict) -> dict:
        docs = await self.retriever.search(prompt)
        answer = await self.llm.answer(prompt, docs=docs)
        return {"text": answer}

# agents/workflow_backend.py
from .base import AbstractBackend, AgentDescriptor, SkillSpec
class WorkflowBackend(AbstractBackend):
    def describe(self) -> AgentDescriptor:
        return AgentDescriptor(
            name="Workflow Orchestrator",
            description="Runs predefined multi-step workflows.",
            streaming=False,
            skills=[SkillSpec(
                id="workflow.run", name="Run Workflow",
                description="Execute a named workflow with parameters.",
                input_modes=["json"], output_modes=["json"], tags=["workflow","batch"]
            )]
        )
    async def run(self, prompt: str, meta: dict) -> dict:
        # expects JSON input {workflow: "...", params: {...}}
        import json; spec = json.loads(prompt)
        result = {"status":"ok","workflow":spec.get("workflow"),"output":{}}
        return {"text": json.dumps(result)}