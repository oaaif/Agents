from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from abc import ABC, abstractmethod

# ---- Per-agent description used to build Agent Card ----
@dataclass
class SkillSpec:
    id: str
    name: str
    description: str
    input_modes: List[str] = field(default_factory=lambda: ["text"])
    output_modes: List[str] = field(default_factory=lambda: ["text"])
    tags: List[str] = field(default_factory=list)

@dataclass
class AgentDescriptor:
    name: str
    version: str = "1.0.0"
    description: str = ""
    streaming: bool = True
    push_notifications: bool = True
    state_transition_history: bool = True
    preferred_transport: str = "jsonrpc"
    additional_interfaces: List[Dict[str, Any]] = field(default_factory=lambda: [{"transport": "jsonrpc", "url": "/"}])
    skills: List[SkillSpec] = field(default_factory=list)

class AbstractBackend(ABC):
    @abstractmethod
    async def run(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        ...

    # New: describe this agent’s capabilities/skills
    @abstractmethod
    def describe(self) -> AgentDescriptor:
        ...