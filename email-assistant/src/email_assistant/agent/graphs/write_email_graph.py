from langgraph.graph import StateGraph, END
from email_assistant.agent.nodes.reply_nodes import (
    router_node,
    generate_draft_node,
    direct_send_node,
    send_email_node,
    send_draft_node,
)
from email_assistant.core.schemas import EmailState


def create_email_graph():
    """
    Create the email writing workflow graph.
    
    Returns:
        Compiled graph for email processing
    """
    # Initialize graph
    workflow = StateGraph(EmailState)
    
    # Add nodes
    workflow.add_node("generate_draft", generate_draft_node)
    workflow.add_node("send_draft", send_draft_node)
    workflow.add_node("direct_send", direct_send_node)
    workflow.add_node("send_email", send_email_node)
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        router_node,
        {
            "generate_draft": "generate_draft",
            "direct_send": "direct_send"
        }
    )
    
    # Generate draft STOPS here (no sending)
    workflow.add_edge("generate_draft", "send_draft")
    workflow.add_edge("send_draft", END)
    
    # Direct send continues to send_email
    workflow.add_edge("direct_send", "send_email")
    workflow.add_edge("send_email", END)
    
    # Compile graph
    return workflow.compile()