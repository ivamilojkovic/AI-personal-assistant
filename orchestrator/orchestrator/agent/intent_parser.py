from langchain_openai import ChatOpenAI
from orchestrator.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4.1-mini", api_key=OPENAI_API_KEY, temperature=0.7)

def detect_intent(user_input: str) -> str:
    prompt = f"""
    Determine user intent: send_email, classify_emails, unknown.

    User: {user_input}
    Respond with only the intent word. 
    """
    out = llm.invoke(prompt).content.strip()
    return out

def extract_email_payload(user_input: str) -> dict:
    prompt = f"""
    Extract as JSON:
    {{
      "recipient": "...",
      "subject": "...",
      "content": "...",
      "send_directly": true/false
    }}

    User: {user_input}
    """

    return llm.invoke(prompt).json()

def extract_date_range(user_input: str) -> dict:
    prompt = f"""
    Extract as JSON:
    {{
      "start_date": "...",
      "end_date": "..."
    }}

    User: {user_input}
    """

    return llm.invoke(prompt).json()
