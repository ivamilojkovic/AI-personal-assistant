from orchestrator.a2a.models import A2ARequest
from orchestrator.a2a.client import send_a2a
from .intent_parser import extract_email_payload, extract_date_range

async def task_send_email(state):
    payload = extract_email_payload(state["user_input"])
    req = A2ARequest(receiver="email-assistant", task="write_and_send_email", payload=payload)
    response = await send_a2a(req)
    return {"result": response.result}

async def task_classify_emails(state):
    payload = extract_date_range(state["user_input"])
    req = A2ARequest(receiver="email-assistant", task="list_and_classify_emails", payload=payload)
    response = await send_a2a(req)
    return {"result": response.result}
