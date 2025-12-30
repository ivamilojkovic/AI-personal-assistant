from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from orchestrator.core.logger import Logger

logger = Logger.get_logger(__name__)


class AgentType(str, Enum):
    """Types of available agents"""
    EMAIL = "email"
    BOOKING = "booking"
    UNKNOWN = "unknown"


@dataclass
class AgentConfig:
    """Configuration for a registered agent"""
    agent_type: AgentType
    name: str
    base_url: str
    description: str
    capabilities: List[str]
    auth_required: bool = False
    auth_token: Optional[str] = None


class AgentRegistry:
    """
    Registry for managing multiple A2A agents.
    
    This allows the orchestrator to route requests to different
    agents based on the user's intent.
    """
    
    def __init__(self):
        """Initialize agent registry"""
        self._agents: Dict[AgentType, AgentConfig] = {}
        logger.info("AgentRegistry initialized")
    
    def register_agent(self, config: AgentConfig) -> None:
        """
        Register an agent in the registry.
        
        Args:
            config: Agent configuration
        """
        self._agents[config.agent_type] = config
        logger.info(f"Registered agent: {config.name} ({config.agent_type})")
        logger.info(f"  Base URL: {config.base_url}")
        logger.info(f"  Capabilities: {config.capabilities}")
    
    def get_agent(self, agent_type: AgentType) -> Optional[AgentConfig]:
        """
        Get agent configuration by type.
        
        Args:
            agent_type: Type of agent to retrieve
            
        Returns:
            Agent configuration or None if not found
        """
        return self._agents.get(agent_type)
    
    def get_all_agents(self) -> List[AgentConfig]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent configurations
        """
        return list(self._agents.values())
    
    def list_capabilities(self) -> Dict[AgentType, List[str]]:
        """
        List all capabilities across all agents.
        
        Returns:
            Dictionary mapping agent types to their capabilities
        """
        return {
            agent_type: config.capabilities
            for agent_type, config in self._agents.items()
        }
    
    def find_agent_for_capability(self, capability: str) -> Optional[AgentConfig]:
        """
        Find an agent that supports a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            Agent configuration or None if no agent supports it
        """
        for config in self._agents.values():
            if capability in config.capabilities:
                return config
        return None
    
    def unregister_agent(self, agent_type: AgentType) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_type: Type of agent to unregister
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_type in self._agents:
            config = self._agents.pop(agent_type)
            logger.info(f"Unregistered agent: {config.name} ({agent_type})")
            return True
        return False
    
    def is_registered(self, agent_type: AgentType) -> bool:
        """
        Check if an agent is registered.
        
        Args:
            agent_type: Type of agent to check
            
        Returns:
            True if registered, False otherwise
        """
        return agent_type in self._agents


def create_default_registry() -> AgentRegistry:
    """
    Create a registry with default agents from environment config.
    
    Returns:
        AgentRegistry with default agents registered
    """
    from orchestrator.config import Config
    
    registry = AgentRegistry()
    
    # Register Email Assistant
    if Config.EMAIL_ASSISTANT_BASE_URL:
        email_config = AgentConfig(
            agent_type=AgentType.EMAIL,
            name="Email Assistant",
            base_url=Config.EMAIL_ASSISTANT_BASE_URL,
            description="AI-powered email management assistant",
            capabilities=[
                "write_email",
                "classify_emails",
            ],
            auth_required=False
        )
        registry.register_agent(email_config)
    
    # Register Booking Manager (if configured)
    if Config.BOOKING_MANAGER_BASE_URL:
        booking_config = AgentConfig(
            agent_type=AgentType.BOOKING,
            name="Booking Manager",
            base_url=Config.BOOKING_MANAGER_BASE_URL,
            description="Booking and reservation management assistant",
            capabilities=[
                "create_booking",
                "list_bookings",
                "cancel_booking",
                "update_booking",
                "check_availability"
            ],
            auth_required=False
        )
        registry.register_agent(booking_config)
    
    logger.info(f"Default registry created with {len(registry.get_all_agents())} agents")
    
    return registry