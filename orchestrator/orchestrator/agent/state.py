from typing import TypedDict, Optional

class OrchestratorState(TypedDict):
    user_input: str
    intent: Optional[str]
    email_task_payload: Optional[dict]
    result: Optional[str]