import asyncio, httpx
from a2a.client.client_factory import ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.client.base_client import ClientConfig

BASE = "http://localhost:8000"

async def pick_agent_by_tag(tag: str):
    async with httpx.AsyncClient(timeout=20) as h:
        idx = (await h.get(f"{BASE}/agents")).json()
        candidates = []
        for item in idx:
            resolver = A2ACardResolver(h, item["rpc_url"].rstrip("/"))  # base is the mount
            card = await resolver.get_agent_card()
            # Card has skills with tags
            if any(tag in (s.get("tags") or []) for s in card.get("skills", [])):
                candidates.append((item, card))
        return candidates

async def talk(agent_mount_url: str, text: str):
    async with httpx.AsyncClient(timeout=30) as h:
        resolver = A2ACardResolver(h, agent_mount_url.rstrip("/"))
        card = await resolver.get_agent_card()
        transport = JsonRpcTransport(agent_mount_url.rstrip("/"), httpx_client=h)
        client = await ClientFactory.create(card, config=ClientConfig(streaming=True), transport=transport)

        message = {
            "taskId": "task_100",
            "messageId": "msg_100",
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
        }
        async for ev in client.send_message(message):
            print("EVENT:", ev)
        await client.close()

async def main():
    mcp_agents = await pick_agent_by_tag("mcp")
    if mcp_agents:
        await talk(mcp_agents[0][0]["rpc_url"], "Hello via MCP")
    else:
        # fallback to echo agent
        await talk(f"{BASE}/agents/echo", "Hello Echo")

if __name__ == "__main__":
    asyncio.run(main())