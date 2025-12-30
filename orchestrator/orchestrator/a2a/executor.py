from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from orchestrator.agent.intent_parser import IntentParser
from orchestrator.agent.graph import OrchestratorGraph
from orchestrator.agent.agent_registry import create_default_registry
from orchestrator.core.logger import Logger
from orchestrator.config import Config

logger = Logger.get_logger(__name__)


class OrchestratorExecutor(AgentExecutor):
    """
    AgentExecutor implementation for Orchestrator.
    
    This executor handles orchestration of operations across multiple agents by:
    1. Parsing user intent
    2. Determining which agent should handle the request
    3. Extracting required parameters
    4. Asking for missing information when needed
    5. Routing to appropriate agent skills
    """
    
    def __init__(self):
        """Initialize orchestrator executor"""
        logger.info("OrchestratorExecutor initializing...")
        
        # Initialize components
        self.intent_parser = IntentParser()
        
        # Initialize agent registry with default agents
        self.agent_registry = create_default_registry()
        
        # Log registered agents
        agents = self.agent_registry.get_all_agents()
        logger.info(f"Registered {len(agents)} agents:")
        for agent in agents:
            logger.info(f"  - {agent.name} ({agent.agent_type}): {agent.base_url}")
        
        # Initialize orchestration graph
        self.graph = OrchestratorGraph(
            intent_parser=self.intent_parser,
            agent_registry=self.agent_registry
        )
        
        logger.info("OrchestratorExecutor initialized successfully")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute orchestration workflow.
        
        Args:
            context: Request context containing user message and metadata
            event_queue: Event queue for sending responses
        """
        try:
            logger.info("=" * 70)
            logger.info("ORCHESTRATOR EXECUTION STARTED")
            logger.info("=" * 70)
            
            # Extract user message
            user_message = context.message
            logger.info(f"User message: {user_message}")
            
            # Get any additional parameters from metadata
            skill_id = context.metadata.get('skill_id', 'orchestrate')
            input_params = context.metadata.get('input_params', {})
            
            # If user provided a 'request' parameter, use that as the message
            if 'request' in input_params:
                user_message = input_params['request']
                logger.info(f"Using 'request' parameter as user message: {user_message}")
            
            logger.info(f"Skill ID: {skill_id}")
            logger.info(f"Input params: {input_params}")
            
            # Run orchestration
            logger.info("Running orchestration workflow...")
            result = await self.graph.run(user_message)
            
            logger.info(f"Orchestration result: {result.success}")
            logger.info(f"Result message: {result.message}")
            
            # Format response message
            response_message = self._format_response(result)
            
            # Send response
            await event_queue.enqueue_event(new_agent_text_message(response_message))
            
            logger.info("Response sent successfully")
            
            logger.info("=" * 70)
            logger.info("ORCHESTRATOR EXECUTION COMPLETED")
            logger.info("=" * 70)
            
        except Exception as e:
            error_msg = f"Error during orchestration: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await event_queue.enqueue_event(new_agent_text_message(error_msg))
    
    def _format_response(self, result) -> str:
        """
        Format orchestration result into response message.
        
        Args:
            result: OrchestrationResult object
            
        Returns:
            Formatted response string
        """
        if result.success:
            response = f"✅ {result.message}\n\n"
            
            # Add agent response details if available
            if result.agent_response:
                response += "**Details:**\n"
                
                # Try to extract meaningful info from agent response
                agent_resp = result.agent_response
                
                # Check for result in various possible locations
                if 'result' in agent_resp:
                    result_data = agent_resp['result']
                    if isinstance(result_data, dict):
                        if 'events' in result_data:
                            for event in result_data['events']:
                                if 'data' in event and 'text' in event['data']:
                                    response += f"{event['data']['text']}\n"
        
        else:
            response = f"❌ {result.message}"
            
            if result.error:
                response += f"\n\n**Error:** {result.error}"
        
        return response
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Cancel the orchestration execution.
        
        Currently not supported.
        
        Args:
            context: Request context
            event_queue: Event queue
            
        Raises:
            Exception: Always raises as cancellation is not supported
        """
        logger.warning("Cancellation requested but not supported")
        error_msg = "Cancellation is not supported for Orchestrator."
        await event_queue.enqueue_event(new_agent_text_message(error_msg))
        raise Exception('cancel not supported')