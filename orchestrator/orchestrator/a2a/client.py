import httpx
from .models import A2ARequest, A2AResponse
from orchestrator.config import EMAIL_AGENT_URL

async def send_a2a(request: A2ARequest) -> A2AResponse:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{EMAIL_AGENT_URL}/a2a",
            json=request.model_dump(),
            timeout=10
        )
        r.raise_for_status()
        return A2AResponse(**r.json())
