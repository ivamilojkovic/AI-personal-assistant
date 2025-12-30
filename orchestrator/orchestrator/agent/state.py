from typing import TypedDict, Annotated, Sequence
from orchestrator.a2a.models import (
    IntentType,
    ParsedIntent,
    OrchestrationResult,
)
from orchestrator.agent.agent_registry import AgentType
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """State for the orchestration graph"""
    messages: Annotated[Sequence[dict], add_messages]
    user_message: str
    parsed_intent: ParsedIntent | None
    target_agent_type: AgentType | None
    awaiting_clarification: bool
    clarification_attempts: int
    result: OrchestrationResult | None

