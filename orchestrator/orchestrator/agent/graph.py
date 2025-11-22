from langgraph.graph import StateGraph, END
from .state import OrchestratorState
from .intent_parser import detect_intent
from .tasks import task_send_email, task_classify_emails

def route(state):
    i = state["intent"]
    if i == "send_email":
        return "send"
    if i == "classify_emails":
        return "classify"
    return END

# Graph
graph = StateGraph(OrchestratorState)

async def parse_intent(state):
    intent = detect_intent(state["user_input"])
    return {"intent": intent}

async def finalize(state):
    return {"result": f"Completed:\n{state['result']}"}

# Register nodes
graph.add_node("parse_intent", parse_intent)
graph.add_conditional_edges("parse_intent", route, {
    "send": "email_send",
    "classify": "email_classify",
    END: END
})

graph.add_node("email_send", task_send_email)
graph.add_node("email_classify", task_classify_emails)

graph.add_edge("email_send", "finalize")
graph.add_edge("email_classify", "finalize")

graph.add_node("finalize", finalize)

graph.set_entry_point("parse_intent")

orchestrator_graph = graph.compile()
