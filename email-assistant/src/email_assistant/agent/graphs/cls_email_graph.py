from langgraph.graph import StateGraph, END
from email_assistant.core.schemas import EmailClassificationState
from email_assistant.agent.nodes.cls_nodes import (
    fetch_email_ids_node,
    classify_single_email_node,
    parallel_classify_node,
    apply_labels_node,
    router_node
)

def create_cls_email_graph():
    """
    Create the unified email classification workflow graph.
    
    Supports two modes in one graph:
    1. Single email classification (listener/webhook)
       Entry -> classify_single -> apply_labels -> END
       
    2. Batch email classification (public API)
       Entry -> fetch_email_ids -> parallel_classify -> apply_labels -> END
    
    Labels are ALWAYS applied (no conditional).
    
    Returns:
        Compiled graph for email classification
    """
    workflow = StateGraph(EmailClassificationState)
    
    # Add nodes
    workflow.add_node("fetch_email_ids", fetch_email_ids_node)
    workflow.add_node("classify_single", classify_single_email_node)
    workflow.add_node("parallel_classify", parallel_classify_node)
    workflow.add_node("apply_labels", apply_labels_node)
    
    # Conditional entry point based on mode
    workflow.set_conditional_entry_point(
        router_node,
        {
            "classify_single": "classify_single",
            "fetch_email_ids": "fetch_email_ids"
        }
    )
    
    # Single mode path: classify -> apply labels
    workflow.add_edge("classify_single", "apply_labels")
    
    # Batch mode path: fetch IDs -> parallel classify -> apply labels
    workflow.add_edge("fetch_email_ids", "parallel_classify")
    workflow.add_edge("parallel_classify", "apply_labels")
    
    # Always end after applying labels
    workflow.add_edge("apply_labels", END)
    
    return workflow.compile()
