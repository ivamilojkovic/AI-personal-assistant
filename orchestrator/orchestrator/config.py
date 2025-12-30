import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    # Server configuration
    HOST = os.getenv("ORCHESTRATOR_HOST", "127.0.0.1")
    PORT = int(os.getenv("ORCHESTRATOR_PORT", "9000"))
    
    # Agent A2A endpoints
    EMAIL_ASSISTANT_BASE_URL = os.getenv("EMAIL_ASSISTANT_BASE_URL", "http://localhost:9001")
    BOOKING_MANAGER_BASE_URL = os.getenv("BOOKING_MANAGER_BASE_URL", "http://localhost:9002")
    
    # Anthropic API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Agent configuration
    ORCHESTRATOR_NAME = "Orchestrator"
    ORCHESTRATOR_VERSION = "1.0.0"
    ORCHESTRATOR_DESCRIPTION = "Intelligent orchestrator for email operations"
    
    # LLM settings
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE", "0.7")
    LLM_MAX_TOKENS = os.getenv("LLM_MAX_TOKENS", "2000")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True