from a2a.types import AgentCard, AgentCapabilities, AgentSkill, AgentInterface
from agents.base import AgentDescriptor

def build_agent_card(base_url: str, mount_prefix: str, desc: AgentDescriptor) -> AgentCard:
    # mount_prefix is something like f"/agents/{agent_id}"
    interfaces = [AgentInterface(transport=i["transport"], url=i["url"]) for i in desc.additional_interfaces]
    skills = [
        AgentSkill(
            id=s.id, name=s.name, description=s.description,
            input_modes=s.input_modes, output_modes=s.output_modes, tags=s.tags
        ) for s in desc.skills
    ]
    return AgentCard(
        name=desc.name,
        version=desc.version,
        description=desc.description,
        url=f"{base_url}{mount_prefix}",
        capabilities=AgentCapabilities(
            streaming=desc.streaming,
            push_notifications=desc.push_notifications,
            state_transition_history=desc.state_transition_history,
        ),
        preferred_transport=desc.preferred_transport,
        additional_interfaces=interfaces,
        skills=skills,
    )