# from agent.graphs.write_email_graph import create_email_graph
from email_assistant.agent.graphs.write_email_graph import create_email_graph
from email_assistant.agent.graphs.cls_email_graph import create_cls_email_graph
from email_assistant.core.schemas import (
    EmailRequest, 
    EmailResponse, 
    EmailState, 
    EmailClassificationState,
    ClassificationRequest,
    ClassificationResponse
)

from fastmcp.client.transports import StdioTransport
from fastmcp import Client

from datetime import datetime
from typing import List
from collections import Counter
from datetime import timedelta

from dotenv import load_dotenv
import os

load_dotenv()

from email_assistant.core.logger import Logger
logger = Logger.get_logger(__name__)

MCP_SERVER_SCRIPT = os.getenv("PATH_GMAIL_MCP_SERVER_SCRIPT", "")

class EmailAssistant:
    """
    AI Email Assistant for:
     1. composing (with AI draft generation) and direct sending emails (raw text)
     2. classifying and labeling emails in inbox
    """
    
    def __init__(self):
        """Initialize the email assistant with the graph workflow"""
        self.graph_writer = create_email_graph()
        self.graph_classifier = create_cls_email_graph()

        # Initialize MCP client once
        self.transport = StdioTransport(
            command="sh",
            args=[MCP_SERVER_SCRIPT]
        )
        logger.info("EmailAssistant initialized (MCP will connect per request)")

    async def _get_mcp_client(self) -> Client:
        """
        Create and connect a new MCP client for this request.
        
        Returns:
            Connected MCP Client
        """
        logger.info("Creating new MCP client session...")
        transport = self.transport
        client = Client(transport)
        
        # Connect the client
        try:
            await client.__aenter__()
            logger.info("MCP client connected successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to connect MCP client: {e}")
            raise


    async def write_email(
        self,
        to: str,
        subject: str,
        text: str = "",
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
        # Create MCP client for this request
        mcp_client = await self._get_mcp_client()
        
        try:
            # Generate subject if missing
            if not subject:
                if text:
                    # Use first few words of text as subject
                    words = text.split()[:5]
                    subject = " ".join(words).capitalize()
                else:
                    subject = "No Subject"
                    
            # Validate and create request
            request = EmailRequest(
                to=to,
                subject=subject,
                text=text,
                tone=tone,
                should_generate=should_generate
            )
            
            # Create initial state from request and add MCP client
            initial_state = request.model_dump()
            initial_state["mcp"] = mcp_client
            
            logger.info(f"Invoking email writer graph for: {to}")
            
            # Run the graph workflow
            result = await self.graph_writer.ainvoke(initial_state)
            
            # Convert result to EmailState for validation
            result_state = EmailState(**result)
            
            logger.info(f"Email writer result: status={result_state.status}")
            
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
            
        except Exception as e:
            logger.error(f"Error in write_email: {e}", exc_info=True)
            return EmailResponse(
                status="error",
                message=f"Failed to process email: {str(e)}",
                error=str(e)
            )
        finally:
            # Always close the MCP client
            try:
                await mcp_client.__aexit__(None, None, None)
                logger.info("MCP client disconnected")
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")
 
    async def classify_emails_batch(
        self,
        after_date: datetime,
        # before_date: datetime,
        categories: List[str],
        max_results: int = 100
    ) -> ClassificationResponse:
        """
        Classify multiple emails in a date range (batch processing).
        
        This method:
        1. Fetches all email IDs in the date range
        2. Classifies each email in PARALLEL using the single classification node
        3. Applies labels to all classified emails
        
        Args:
            after_date: Start date for email retrieval
            before_date: End date for email retrieval
            categories: List of predefined categories (must match Gmail label names)
            max_results: Maximum number of emails to process
            
        Returns:
            ClassificationResponse with batch classification results
            
        Example:
            classifier = EmailClassifier()
            response = await classifier.classify_emails_batch(
                after_date=datetime(2024, 11, 1),
                before_date=datetime(2024, 11, 18),
                categories=["Work", "Personal", "Newsletter", "Spam"],
                max_results=50
            )
            print(f"Classified {response.total_classified} emails")
        """
        
        # Create MCP client for this request
        mcp_client = await self._get_mcp_client()
        
        try:
            # Create initial state for batch mode
            initial_state = {
                "mode": "batch",
                "after_date": after_date,
                "categories": categories,
                "max_results": max_results,
                "mcp": mcp_client
            }
            
            logger.info(f"Invoking email classifier graph: {len(categories)} categories, max {max_results} emails")
            
            # Run the graph workflow in batch mode
            result = await self.graph_classifier.ainvoke(initial_state)
            
            # Convert result to state for validation
            result_state = EmailClassificationState(**result)
            
            logger.info(f"Classification result: status={result_state.status}, classified={result_state.total_classified}")
            
            # Create response message
            if result_state.status in ["classification_complete", "labels_applied"]:
                message = f"Classified {result_state.total_classified} emails in parallel"
                
                if result_state.labeled_count:
                    message += f", applied {result_state.labeled_count} labels"
            else:
                message = f"Classification failed: {result_state.error}"
            
            return ClassificationResponse(
                status=result_state.status,
                message=message,
                total_emails=result_state.total_emails,
                total_classified=result_state.total_classified,
                classification_results=result_state.classification_results,
                labeled_count=result_state.labeled_count,
                error=result_state.error
            )
            
        except Exception as e:
            logger.error(f"Error in classify_emails_batch: {e}", exc_info=True)
            return ClassificationResponse(
                status="error",
                message=f"Failed to classify emails: {str(e)}",
                error=str(e)
            )
        finally:
            # Always close the MCP client
            try:
                await mcp_client.__aexit__(None, None, None)
                logger.info("MCP client disconnected")
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")
    
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

        # # Example 1: Direct send (no generation)
        # print("Example 1: Direct Send")
        # result1 = await assistant.write_email(
        #     to="iva97.ja@gmail.com",
        #     subject="Meeting Tomorrow",
        #     text="Hi, just confirming our meeting tomorrow at 2 PM. See you then!",
        #     should_generate=False
        # )
        # print(f"Status: {result1.status}")
        # print(f"Message: {result1.message}")
        # print("-" * 50)
        
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

        categories = ["Work", "Personal", "Newsletter"]

        # Example 3: Classify last 7 days
        print("=" * 60)
        print("Example 1: Batch Classification (Last 7 Days)")
        print("=" * 60)

        logging.info(f"Starting batch email classification between {datetime.now() - timedelta(days=7)} and {datetime.now()}")
        
        result3 = await assistant.classify_emails_batch(
            after_date=datetime.now() - timedelta(days=7),
            # before_date=datetime.now(),
            categories=categories,
            max_results=20
        )
        
        print(f"Status: {result3.status}")
        print(f"Message: {result3.message}")
        print(f"Total classified: {result3.total_classified}")
        print(f"Labels applied: {result3.labeled_count}")

        if result3.classification_results:
            result = result3.classification_results[0]
            category_counts = Counter(
                res['category'] for res in result.get('classification_results')
            )
            print("\nClassification Summary:")
            for category, count in category_counts.items():
                print(f"  {category}: {count} emails")
        
        print("-" * 60)
        

    # Run examples
    asyncio.run(main())
        
