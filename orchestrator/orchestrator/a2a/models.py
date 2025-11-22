from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime

class A2ARequest(BaseModel):
    version: str = "1.0"
    sender: str = "orchestrator"
    receiver: str
    task: str
    payload: Dict[str, Any]
    timestamp: str = datetime.now(datetime.timezone.utc).isoformat()

class A2AResponse(BaseModel):
    version: str = "1.0"
    sender: str
    receiver: str = "orchestrator"
    status: str
    result: Dict[str, Any]
    timestamp: str = datetime.now(datetime.timezone.utc).isoformat()
