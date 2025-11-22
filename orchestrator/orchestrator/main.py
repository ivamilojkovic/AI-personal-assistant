from fastapi import FastAPI
from orchestrator.agent.graph import orchestrator_graph

app = FastAPI()

@app.post("/orchestrate")
async def orchestrate(data: dict):
    result = await orchestrator_graph.invoke({"user_input": data["user_input"]})
    return result
