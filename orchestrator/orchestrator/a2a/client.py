from typing import Any, Dict, Optional
from uuid import uuid4
import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

from orchestrator.core.logger import Logger
from orchestrator.agent.agent_registry import AgentConfig

logger = Logger.get_logger(__name__)


class A2AClient:
    """
    Generic client for communicating with any A2A agent.
    
    This client can connect to any agent that implements the A2A protocol,
    making the orchestrator truly agent-agnostic.
    """
    
    def __init__(self, agent_config: AgentConfig):
        """
        Initialize generic A2A client.
        
        Args:
            agent_config: Configuration for the agent to connect to
        """
        self.agent_config = agent_config
        self._client: Optional[A2AClient] = None
        self._httpx_client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"A2AClient initialized for {agent_config.name}")
        logger.info(f"  Base URL: {agent_config.base_url}")
        logger.info(f"  Capabilities: {agent_config.capabilities}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Establish connection to the agent"""
        if self._client is not None:
            return
        
        logger.info(f"Connecting to {self.agent_config.name}...")
        
        self._httpx_client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize card resolver
        resolver = A2ACardResolver(
            httpx_client=self._httpx_client,
            base_url=self.agent_config.base_url,
        )
        
        # Fetch agent card
        try:
            if self.agent_config.auth_required and self.agent_config.auth_token:
                # Try to get extended card with authentication
                logger.info("Fetching extended agent card with authentication...")
                auth_headers = {'Authorization': f'Bearer {self.agent_config.auth_token}'}
                agent_card = await resolver.get_agent_card(
                    relative_card_path='/.well-known/agent.json',
                    http_kwargs={'headers': auth_headers}
                )
            else:
                # Get public card
                logger.info("Fetching public agent card...")
                agent_card = await resolver.get_agent_card()
            
            logger.info(f"Successfully fetched agent card: {agent_card.agent.name}")
            logger.info(f"Available skills: {[skill.id for skill in agent_card.skills]}")
            
            # Initialize A2A client
            self._client = A2AClient(
                httpx_client=self._httpx_client,
                agent_card=agent_card
            )
            
            logger.info(f"{self.agent_config.name} client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.agent_config.name}: {e}")
            if self._httpx_client:
                await self._httpx_client.aclose()
            raise
    
    async def close(self):
        """Close connection"""
        if self._httpx_client:
            await self._httpx_client.aclose()
            self._httpx_client = None
            self._client = None
            logger.info(f"{self.agent_config.name} client connection closed")
    
    async def call_skill(
        self,
        skill_id: str,
        input_params: Dict[str, Any],
        message_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call a skill on the agent.
        
        Args:
            skill_id: ID of the skill to call
            input_params: Parameters for the skill
            message_text: Optional message text
            
        Returns:
            Response from the agent
            
        Raises:
            RuntimeError: If client is not connected
            Exception: If skill execution fails
        """
        if not self._client:
            raise RuntimeError("Client not connected. Call connect() first or use as async context manager.")
        
        logger.info(f"Calling skill '{skill_id}' on {self.agent_config.name}")
        logger.info(f"Parameters: {input_params}")
        
        # Create message payload
        send_message_payload: Dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': message_text or f"Execute {skill_id}"
                    }
                ],
                'messageId': uuid4().hex,
            },
            'metadata': {
                'skill_id': skill_id,
                'input_params': input_params
            }
        }
        
        # Create request
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        try:
            # Send message
            logger.info(f"Sending message to {self.agent_config.name}...")
            response = await self._client.send_message(request)
            
            logger.info(f"Received response from {self.agent_config.name}")
            
            # Extract response data
            response_dict = response.model_dump(mode='json', exclude_none=True)
            
            return response_dict
            
        except Exception as e:
            logger.error(f"Error calling skill {skill_id} on {self.agent_config.name}: {e}", exc_info=True)
            raise
    
    def supports_skill(self, skill_id: str) -> bool:
        """
        Check if the agent supports a specific skill.
        
        Args:
            skill_id: Skill ID to check
            
        Returns:
            True if skill is supported, False otherwise
        """
        return skill_id in self.agent_config.capabilities


class AgentClientFactory:
    """
    Factory for creating agent clients.
    """
    
    @staticmethod
    def create_client(agent_config: AgentConfig) -> A2AClient:
        """
        Create a client for the specified agent.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            A2AClient instance
        """
        return A2AClient(agent_config)