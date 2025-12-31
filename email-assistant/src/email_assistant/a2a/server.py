import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from email_assistant.a2a.executor import EmailAgentExecutor
from .cards import public_agent_card, extended_agent_card

from email_assistant.core.logger import Logger
logger = Logger.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Email Assistant A2A Server",
    description="A2A protocol server for AI email assistant",
    version="1.0.0"
)

def is_authenticated(request: Request) -> bool:
    """
    Check if the request is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if authenticated, False otherwise
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # TODO: Implement proper token validation here
        # For now, just check if Bearer token exists
        return True
    return False


def get_agent_card(request: Request):
    """
    Return appropriate agent card based on authentication status.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Agent card (public or extended)
    """
    if is_authenticated(request):
        logger.info("Returning extended agent card (authenticated user)")
        return extended_agent_card
    else:
        logger.info("Returning public agent card (unauthenticated)")
        return public_agent_card

# Create a default request handler
request_handler = DefaultRequestHandler(
    agent_executor=EmailAgentExecutor(),
    task_store=InMemoryTaskStore()
)


# Create A2A server instances for both cards
server = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=request_handler,
    extended_agent_card=extended_agent_card
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "email-assistant-a2a"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Email Assistant A2A Server (Google A2A Protocol)",
        "version": "1.0.0",
        "protocol": "Google A2A",
        "endpoints": {
            "agent_card": "/.well-known/agent.json",
            "invoke": "/invoke",
            "health": "/health"
        }
    }

@app.get("/.well-known/agent.json")
async def get_agent_card_endpoint(request: Request):
    """
    A2A discovery endpoint - returns agent card.
    Returns different cards based on authentication status.
    """
    agent_card = get_agent_card(request)
    return JSONResponse(content=agent_card.model_dump())

app.mount("/", server.build())

if __name__ == "__main__":
    logger.info("Starting Email Assistant A2A Server...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9001,
        log_level="info"
    )