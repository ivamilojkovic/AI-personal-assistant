from .sender import write_and_send
from agent.interface import EmailAssistant

async def handle_email_request(task: str, payload: dict):
    email_assistant = EmailAssistant()
    if task == "write_and_send_email":
        return await email_assistant.write_email(payload)
    if task == "list_and_classify_emails":
        return await email_assistant.classify_emails_batch(payload)
    raise ValueError(f"Unknown task {task}")
