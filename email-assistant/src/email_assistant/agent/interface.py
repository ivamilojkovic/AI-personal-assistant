# from agent.graphs.write_email_graph import create_email_graph
from email_assistant.agent.graphs.write_email_graph import create_email_graph
from email_assistant.core.schemas import EmailRequest, EmailResponse, EmailState

class EmailAssistant:
    """
    AI Email Assistant for composing and sending emails.
    Supports both direct sending and AI-powered draft generation.
    """
    
    def __init__(self):
        """Initialize the email assistant with the graph workflow"""
        self.graph = create_email_graph()
    
    async def write_email(
        self,
        to: str,
        subject: str,
        text: str,
        tone: str = "professional",
        should_generate: bool = False
    ) -> EmailResponse:
        """
        Write and send an email via the agent workflow.
        
        This method provides A2A (Application-to-Application) interface
        for email composition and sending.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            text: Email body content or instructions for generation
            tone: Tone of the email (professional, casual, formal, friendly)
            should_generate: If True, uses text as instructions to generate email.
                           If False, uses text as-is for email body.
        
        Returns:
            EmailResponse with status, message, and generated content
            
        Example:
            assistant = EmailAssistant()
            
            # Direct send
            response = await assistant.write_email(
                to="colleague@example.com",
                subject="Meeting Tomorrow",
                text="Hi, confirming our 2 PM meeting tomorrow.",
                should_generate=False
            )
            
            # Generate draft
            response = await assistant.write_email(
                to="client@example.com",
                subject="Project Update",
                text="Tell client project is 80% done, on schedule for next week",
                tone="professional",
                should_generate=True
            )
        """
        # Validate and create request
        request = EmailRequest(
            to=to,
            subject=subject,
            text=text,
            tone=tone,
            should_generate=should_generate
        )
        
        # Create initial state from request
        initial_state = EmailState(**request.model_dump())
        
        # Run the graph workflow
        result = await self.graph.ainvoke(initial_state.model_dump())
        
        # Convert result to EmailState for validation
        result_state = EmailState(**result)
        
        # Create response
        if result_state.status == "sent_successfully":
            message = f"Email sent successfully to {result_state.to}"
        elif result_state.status == "draft_generated":
            message = "Email draft generated successfully"
        elif result_state.status == "sent_directly":
            message = f"Email sent directly to {result_state.to}"
        else:
            message = f"Error: {result_state.error}"
        
        return EmailResponse(
            status=result_state.status,
            message=message,
            generated_body=result_state.generated_body,
            error=result_state.error
        )
    
    def write_email_sync(
        self,
        to: str,
        subject: str,
        text: str,
        tone: str = "professional",
        should_generate: bool = False
    ) -> EmailResponse:
        """
        Synchronous version of write_email for non-async contexts.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            text: Email body content or instructions
            tone: Tone of the email
            should_generate: Whether to generate draft or use text as-is
            
        Returns:
            EmailResponse with status and details
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.write_email(to, subject, text, tone, should_generate)
        )


# Example usage and testing
if __name__ == "__main__":

    import logging
    import time

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(pathname)s] (+%(relativeCreated)d ms) %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    import asyncio
    
    async def main():
        # Initialize assistant
        assistant = EmailAssistant()

        # Example 1: Direct send (no generation)
        print("Example 1: Direct Send")
        result1 = await assistant.write_email(
            to="iva97.ja@gmail.com",
            subject="Meeting Tomorrow",
            text="Hi, just confirming our meeting tomorrow at 2 PM. See you then!",
            should_generate=False
        )
        print(f"Status: {result1.status}")
        print(f"Message: {result1.message}")
        print("-" * 50)
        
        # # Example 2: Generate draft
        # print("\nExample 2: Generate Draft")
        # result2 = await assistant.write_email(
        #     to="iva97.ja@gmail.com",
        #     subject="Project Update",
        #     text="Inform the client that the project is 80% complete, on schedule, and we'll deliver next week. Mention the new features added.",
        #     tone="professional",
        #     should_generate=True
        # )
        # print(f"Status: {result2.status}")
        # print(f"Message: {result2.message}")
        # if result2.generated_body:
        #     print(f"Generated Body:\n{result2.generated_body}")
        # print("-" * 50)

    # Run examples
    asyncio.run(main())
        
