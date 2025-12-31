import json
from typing import Dict, Any, Optional

from orchestrator.a2a.models import (
    IntentType, 
    ParsedIntent
)
from orchestrator.config import Config
from orchestrator.core.logger import Logger
from orchestrator.agent.prompts import SYSTEM_PROMPT

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


logger = Logger.get_logger(__name__)


class IntentParser:
    """
    Parse user intents using Claude LLM.
    """
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize intent parser.
        
        Args:
            api_key:OPEN AI key (uses Config.OPENAI_API_KEY if not provided)
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = ChatOpenAI(
            model=Config.LLM_MODEL, 
            api_key=self.api_key,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS
        )
        logger.info("IntentParser initialized")
    
    async def parse(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """
        Parse user message to extract intent and parameters.
        
        Args:
            user_message: User's natural language message
            context: Optional conversation context
            
        Returns:
            ParsedIntent object with intent, parameters, and missing info
        """
        logger.info(f"Parsing user message: {user_message[:100]}...")
        
        # Build prompt with context if available
        prompt = f"User message: {user_message}"
        if context:
            prompt = f"Previous context: {json.dumps(context)}\n\n{prompt}"

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        try:
            # Call LLM API
            response = await self.client.ainvoke(messages)
            
            # Extract response text
            response_text = response.content
            logger.info(f"LLM response: {response_text}")
            
            # Parse JSON response
            try:
                result_dict = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                    result_dict = json.loads(response_text)
                else:
                    raise
            
            # Convert to ParsedIntent
            parsed_intent = ParsedIntent(**result_dict)
            
            logger.info(f"Parsed intent: {parsed_intent.intent}, confidence: {parsed_intent.confidence}")
            if parsed_intent.missing_parameters:
                logger.info(f"Missing parameters: {parsed_intent.missing_parameters}")
            
            return parsed_intent
            
        except Exception as e:
            logger.error(f"Error parsing intent: {e}", exc_info=True)
            # Return unknown intent on error
            return ParsedIntent(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                clarification_needed=True,
                clarification_message=f"I encountered an error understanding your request: {str(e)}"
            )
    
    def validate_parameters(self, intent: IntentType, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that all required parameters are present for the intent.
        
        Args:
            intent: Parsed intent type
            parameters: Extracted parameters
            
        Returns:
            Tuple of (is_valid, missing_parameters)
        """
        missing = []
        
        # Email intents
        if intent == IntentType.WRITE_EMAIL:
            if not parameters.get('to'):
                missing.append('to')
        
        elif intent == IntentType.CLASSIFY_EMAILS:
            if not parameters.get('categories'):
                missing.append('categories')
        
        # Booking intents
        elif intent == IntentType.CREATE_BOOKING:
            if not parameters.get('service'):
                missing.append('service')
            if not parameters.get('date'):
                missing.append('date')
            if not parameters.get('time'):
                missing.append('time')
        
        elif intent == IntentType.CANCEL_BOOKING:
            if not parameters.get('booking_id'):
                missing.append('booking_id')
        
        elif intent == IntentType.UPDATE_BOOKING:
            if not parameters.get('booking_id'):
                missing.append('booking_id')
        
        elif intent == IntentType.CHECK_AVAILABILITY:
            if not parameters.get('service'):
                missing.append('service')
            if not parameters.get('date'):
                missing.append('date')
        
        # LIST_BOOKINGS has no required parameters (all optional)
        
        is_valid = len(missing) == 0
        return is_valid, missing