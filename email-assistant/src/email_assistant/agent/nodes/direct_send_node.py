from email_assistant.core.schemas import EmailState

def direct_send_node(state: EmailState) -> dict:
    """
    Directly send email using provided text without generation.
    
    Args:
        state: Current email state
        
    Returns:
        Updated state after sending
    """
    try:
        # Use the provided text as-is
        body = state.text
        
        return {
            **state.model_dump(),
            "generated_body": body,
            "status": "sent_directly"
        }
    
    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to perform direct_send_email: {str(e)}"
        }
