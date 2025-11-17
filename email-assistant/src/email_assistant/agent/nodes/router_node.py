from typing import Literal
from email_assistant.core.schemas import EmailState

def router_node(state: EmailState) -> Literal["generate_draft", "direct_send"]:
    """
    Router node that decides whether to generate a draft or send directly.
    
    Args:
        state: Current email state
        
    Returns:
        Next node to execute
    """
    if state.should_generate:
        return "generate_draft"
    return "direct_send"