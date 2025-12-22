from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from email_assistant.agent.interface import EmailAssistant

from datetime import timedelta, datetime

from email_assistant.core.logger import Logger
logger = Logger.get_logger(__name__)

class EmailAgentExecutor(AgentExecutor):
    """
    AgentExecutor implementation for Email Assistant.
    
    This executor handles two main skills:
    1. write_email - Compose and send emails with optional AI generation
    2. classify_emails - Classify and label emails in batch
    """
    def __init__(self):
        logger.info("EmailAssistantExecutor initialized")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            print(">>> EXECUTOR CALLED <<<")
            print(f"Context Metadata: {context.metadata}")
            print(f"Skill ID: {context.metadata.get('skill_id')}")
         
            skill_id = context.metadata.get('skill_id', "")
            # input_text = context.message
            input_params = context.metadata.get('input_params', {})
            
            logger.info(f"Executing skill: {skill_id}")
            # logger.info(f"Input text: {input_text[:100]}...")

            # Initialize EmailAssistant per request to avoid MCP session issues
            logger.info("Initializing EmailAssistant for this request...")
            agent = EmailAssistant()
            
            if skill_id == "write_email":
                to = input_params.get("to")
                subject = input_params.get("subject", "")
                text = input_params.get("text", "") 
                tone = input_params.get("tone", "professional")
                should_generate = input_params.get("should_generate", True)
                
                if not to:
                    raise ValueError("Missing required parameter: 'to' (recipient email address)")
                
                result = await agent.write_email(
                    to=to,
                    subject=subject,
                    text=text,
                    tone=tone,
                    should_generate=should_generate
                )
                
                print(">>> EMAIL WRITE RESULT <<<")
                print(result)   

                output_text = result.message
                if result.generated_body:
                    output_text += f"\n\nGenerated Email:\n{result.generated_body}"
                await event_queue.enqueue_event(new_agent_text_message(output_text))
                logger.info(f"Successfully executed skill: {skill_id}")
            
            elif skill_id == "classify_emails":
                days_back = input_params.get("days_back", 7)
                categories = input_params.get("categories", [])
                
                if not days_back or not categories:
                    raise ValueError("Missing required parameters: 'days_back' and/or 'categories'")
                
                result = await agent.classify_emails_batch(
                    after_date=datetime.now() - timedelta(days=days_back),
                    # before_date=datetime.now(),
                    categories=categories,
                    max_results=20
                )

                print(">>> EMAIL CLASSIFY RESULT <<<")
                print(result)   
                
                await event_queue.enqueue_event(new_agent_text_message(result.message))
                logger.info(f"Successfully executed skill: {skill_id}")

        except Exception as e:
            error_msg = f"Error executing skill: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await event_queue.enqueue_event(new_agent_text_message(error_msg))
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Cancel the agent's execution.
        
        Currently not supported for this agent.

        Args:
            context: Request context
            event_queue: Event queue
            
        Raises:
            Exception: Always raises as cancellation is not supported
        """
        logger.warning("Cancellation requested but not supported")
        error_msg = (
            "Cancellation is not supported for Email Assistant. "
        )
        await event_queue.enqueue_event(new_agent_text_message(error_msg))
        raise Exception('cancel not supported')

