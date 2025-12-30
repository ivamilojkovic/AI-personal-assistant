from langgraph.graph import StateGraph, END

from orchestrator.agent.intent_parser import IntentParser
from orchestrator.agent.agent_registry import AgentRegistry, AgentType
from orchestrator.a2a.client import AgentClientFactory
from orchestrator.a2a.models import (
    IntentType,
    OrchestrationResult,
)
from orchestrator.agent.state import GraphState
from orchestrator.core.logger import Logger

logger = Logger.get_logger(__name__)

class OrchestratorGraph:
    """
    LangGraph-based orchestration workflow with multi-agent routing.
    
    The graph follows this flow:
    1. parse_intent: Parse user message to extract intent and parameters
    2. determine_agent: Determine which agent should handle the request
    3. check_parameters: Check if all required parameters are present
    4. execute_skill: Call the appropriate agent's skill
    5. format_response: Format the final response
    """
    
    # Map intents to agent types
    INTENT_TO_AGENT = {
        IntentType.WRITE_EMAIL: AgentType.EMAIL,
        IntentType.CLASSIFY_EMAILS: AgentType.EMAIL,
        IntentType.CREATE_BOOKING: AgentType.BOOKING,
        IntentType.LIST_BOOKINGS: AgentType.BOOKING,
        IntentType.CANCEL_BOOKING: AgentType.BOOKING,
        IntentType.UPDATE_BOOKING: AgentType.BOOKING,
        IntentType.CHECK_AVAILABILITY: AgentType.BOOKING,
        IntentType.UNKNOWN: AgentType.UNKNOWN,
    }
    
    def __init__(self, intent_parser: IntentParser, agent_registry: AgentRegistry):
        """
        Initialize orchestrator graph.
        
        Args:
            intent_parser: Intent parser instance
            agent_registry: Registry of available agents
        """
        self.intent_parser = intent_parser
        self.agent_registry = agent_registry
        self.graph = self._build_graph()
        logger.info("OrchestratorGraph initialized with multi-agent support")
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestration graph"""
        
        # Create graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("parse_intent", self._parse_intent_node)
        workflow.add_node("determine_agent", self._determine_agent_node)
        workflow.add_node("check_parameters", self._check_parameters_node)
        workflow.add_node("execute_skill", self._execute_skill_node)
        workflow.add_node("format_response", self._format_response_node)
        
        # Add edges
        workflow.set_entry_point("parse_intent")
        workflow.add_edge("parse_intent", "determine_agent")
        workflow.add_edge("determine_agent", "check_parameters")
        
        # Conditional edge from check_parameters
        workflow.add_conditional_edges(
            "check_parameters",
            self._should_execute_or_clarify,
            {
                "execute": "execute_skill",
                "clarify": "format_response",
                "error": "format_response"
            }
        )
        
        workflow.add_edge("execute_skill", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def _parse_intent_node(self, state: GraphState) -> GraphState:
        """Parse user intent from message"""
        logger.info("Node: parse_intent")
        
        user_message = state["user_message"]
        
        # Parse intent
        parsed_intent = await self.intent_parser.parse(user_message)
        
        state["parsed_intent"] = parsed_intent
        state["awaiting_clarification"] = parsed_intent.clarification_needed
        
        return state
    
    async def _determine_agent_node(self, state: GraphState) -> GraphState:
        """Determine which agent should handle the request"""
        logger.info("Node: determine_agent")
        
        parsed_intent = state["parsed_intent"]
        
        if not parsed_intent:
            state["target_agent_type"] = AgentType.UNKNOWN
            return state
        
        # Map intent to agent type
        agent_type = self.INTENT_TO_AGENT.get(parsed_intent.intent, AgentType.UNKNOWN)
        state["target_agent_type"] = agent_type
        
        logger.info(f"Target agent determined: {agent_type}")
        
        # Check if agent is registered
        if agent_type != AgentType.UNKNOWN:
            agent_config = self.agent_registry.get_agent(agent_type)
            if not agent_config:
                logger.warning(f"Agent {agent_type} not registered!")
                state["result"] = OrchestrationResult(
                    success=False,
                    message=f"The {agent_type} agent is not currently available. Please try again later.",
                    intent=parsed_intent.intent,
                    error=f"Agent {agent_type} not registered"
                )
        
        return state
    
    async def _check_parameters_node(self, state: GraphState) -> GraphState:
        """Check if all required parameters are present"""
        logger.info("Node: check_parameters")
        
        parsed_intent = state["parsed_intent"]
        
        if not parsed_intent:
            state["result"] = OrchestrationResult(
                success=False,
                message="Failed to parse intent",
                intent=IntentType.UNKNOWN,
                error="No parsed intent available"
            )
            return state
        
        # Validate parameters
        is_valid, missing = self.intent_parser.validate_parameters(
            parsed_intent.intent,
            parsed_intent.parameters
        )
        
        if not is_valid or parsed_intent.missing_parameters:
            all_missing = list(set(missing + parsed_intent.missing_parameters))
            parsed_intent.missing_parameters = all_missing
            parsed_intent.clarification_needed = True
            
            if not parsed_intent.clarification_message:
                parsed_intent.clarification_message = (
                    f"I need the following information to proceed: "
                    f"{', '.join(all_missing)}. Please provide them."
                )
            
            state["awaiting_clarification"] = True
            state["parsed_intent"] = parsed_intent
        
        return state
    
    def _should_execute_or_clarify(self, state: GraphState) -> str:
        """Determine whether to execute skill or ask for clarification"""
        parsed_intent = state.get("parsed_intent")
        
        if not parsed_intent:
            return "error"
        
        if state.get("result") is not None:
            # Already have an error result (e.g., agent not available)
            return "error"
        
        if parsed_intent.intent == IntentType.UNKNOWN:
            return "clarify"
        
        if state.get("awaiting_clarification", False):
            return "clarify"
        
        return "execute"
    
    async def _execute_skill_node(self, state: GraphState) -> GraphState:
        """Execute the appropriate agent skill"""
        logger.info("Node: execute_skill")
        
        parsed_intent = state["parsed_intent"]
        agent_type = state.get("target_agent_type")
        
        if not parsed_intent or not agent_type:
            state["result"] = OrchestrationResult(
                success=False,
                message="No intent or agent determined",
                intent=IntentType.UNKNOWN,
                error="Missing intent or agent"
            )
            return state
        
        # Get agent configuration
        agent_config = self.agent_registry.get_agent(agent_type)
        if not agent_config:
            state["result"] = OrchestrationResult(
                success=False,
                message=f"Agent {agent_type} is not available",
                intent=parsed_intent.intent,
                error=f"Agent {agent_type} not found in registry"
            )
            return state
        
        try:
            intent = parsed_intent.intent
            params = parsed_intent.parameters
            skill_id = intent.value  # Use intent value as skill_id
            
            logger.info(f"Executing intent: {intent} via {agent_config.name}")
            logger.info(f"Skill: {skill_id}")
            logger.info(f"Parameters: {params}")
            
            # Create client for the target agent
            client = AgentClientFactory.create_client(agent_config)
            
            try:
                # Connect and call skill
                await client.connect()
                
                response = await client.call_skill(
                    skill_id=skill_id,
                    input_params=params,
                    message_text=state["user_message"]
                )
                
                state["result"] = OrchestrationResult(
                    success=True,
                    message=f"Successfully executed {intent.value}",
                    intent=intent,
                    agent_response=response
                )
                
            finally:
                await client.close()
            
        except Exception as e:
            logger.error(f"Error executing skill: {e}", exc_info=True)
            state["result"] = OrchestrationResult(
                success=False,
                message=f"Error executing skill: {str(e)}",
                intent=parsed_intent.intent,
                error=str(e)
            )
        
        return state
    
    async def _format_response_node(self, state: GraphState) -> GraphState:
        """Format the final response"""
        logger.info("Node: format_response")
        
        # If we need clarification, format clarification message
        if state.get("awaiting_clarification", False):
            parsed_intent = state.get("parsed_intent")
            if parsed_intent and parsed_intent.clarification_message:
                state["result"] = OrchestrationResult(
                    success=False,
                    message=parsed_intent.clarification_message,
                    intent=parsed_intent.intent,
                    error="Clarification needed"
                )
        
        # Result should already be set by execute_skill_node if we got there
        # If not set, create a default error result
        if not state.get("result"):
            state["result"] = OrchestrationResult(
                success=False,
                message="Unable to process request",
                intent=IntentType.UNKNOWN,
                error="No result generated"
            )
        
        return state
    
    async def run(self, user_message: str) -> OrchestrationResult:
        """
        Run the orchestration workflow.
        
        Args:
            user_message: User's natural language message
            
        Returns:
            OrchestrationResult with execution details
        """
        logger.info(f"Running orchestration for message: {user_message[:100]}...")
        
        # Initialize state
        initial_state: GraphState = {
            "messages": [],
            "user_message": user_message,
            "parsed_intent": None,
            "target_agent_type": None,
            "awaiting_clarification": False,
            "clarification_attempts": 0,
            "result": None,
        }
        
        # Run graph
        final_state = await self.graph.ainvoke(initial_state)
        
        result = final_state.get("result")
        
        if not result:
            result = OrchestrationResult(
                success=False,
                message="Orchestration failed",
                intent=IntentType.UNKNOWN,
                error="No result produced"
            )
        
        logger.info(f"Orchestration completed: success={result.success}")
        if final_state.get("target_agent_type"):
            logger.info(f"Target agent: {final_state['target_agent_type']}")
        
        return result