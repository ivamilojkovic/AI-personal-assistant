import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orchestrator.a2a.executor import OrchestratorExecutor
from orchestrator.a2a.cards import public_agent_card, extended_agent_card
from orchestrator.core.logger import Logger
from orchestrator.config import Config

logger = Logger.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Orchestrator A2A Server",
    description="A2A protocol server for email orchestration",
    version=Config.ORCHESTRATOR_VERSION
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
    agent_executor=OrchestratorExecutor(),
    task_store=InMemoryTaskStore()
)


# Create A2A server instance
server = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=request_handler,
    extended_agent_card=extended_agent_card
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator-a2a",
        "version": Config.ORCHESTRATOR_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Orchestrator A2A Server",
        "version": Config.ORCHESTRATOR_VERSION,
        "protocol": "Google A2A",
        "description": "Intelligent orchestrator for email operations",
        "endpoints": {
            "agent_card": "/.well-known/agent.json",
            "invoke": "/invoke",
            "health": "/health"
        },
        "capabilities": [
            "Natural language understanding",
            "Intent parsing",
            "Parameter extraction",
            "Email assistant orchestration"
        ]
    }


@app.get("/.well-known/agent.json")
async def get_agent_card_endpoint(request: Request):
    """
    A2A discovery endpoint - returns agent card.
    Returns different cards based on authentication status.
    """
    agent_card = get_agent_card(request)
    return JSONResponse(content=agent_card.model_dump())


def start_server():
    """Start the A2A server"""
    logger.info("=" * 70)
    logger.info("STARTING ORCHESTRATOR A2A SERVER")
    logger.info("=" * 70)
    logger.info(f"Host: {Config.HOST}")
    logger.info(f"Port: {Config.PORT}")
    logger.info(f"Email Assistant URL: {Config.EMAIL_ASSISTANT_BASE_URL}")
    logger.info("=" * 70)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set OPENAI API KEY environment variable")
        return
    
    uvicorn.run(
        server.build(),
        host=Config.HOST,
        port=Config.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()