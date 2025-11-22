from email_assistant.core.schemas import EmailClassificationState
from typing import List, Dict, Any
from datetime import datetime
import asyncio

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os, json
from email import message_from_string

from email_assistant.core.logger import Logger

logger = Logger.get_logger(__name__)

load_dotenv

async def fetch_email_ids_node(state: EmailClassificationState) -> dict:
    """
    Fetch all email IDs between given dates for batch classification.
    This replaces the old fetch_emails_batch_node.
    """
    try:
        logger.info("Fetching email IDs for classification...")

        client = state.mcp
        
        # Format dates to YYYY/MM/DD as required by the server
        after_date = state.after_date.strftime("%Y/%m/%d") if state.after_date else None
        before_date = state.before_date.strftime("%Y/%m/%d") if state.before_date else None

        # Call the search_emails tool
        async with client:
            # result = await client.call_tool("search_emails", {
            result = await client.call_tool("search_unlabeled_emails", {
                "after_date": after_date or None,
                # "before_date": before_date or None,
                "max_results": state.max_results or 100
            })
        
        # Parse the result string to extract message IDs
        # The result format is: "Message ID: {msg_id}\nFrom: ...\nSubject: ...\n"
        email_ids = []
        lines = result.content[0].text.split('\n') if hasattr(result, 'content') else str(result).split('\n')
        
        for line in lines:
            if line.strip().startswith("Message ID:"):
                msg_id = line.split("Message ID:")[1].strip()
                email_ids.append(msg_id)

        logger.info(f"Fetched {email_ids} email IDs for classification.")
        
        return {
            "email_ids": email_ids,
            "total_emails": len(email_ids),
            "status": "email_ids_fetched"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to fetch email IDs: {e}"
        }


async def classify_single_email_node(state: EmailClassificationState) -> dict:
    """
    Classify a SINGLE email by ID.
    This node is reusable for both:
    1. Real-time classification (when listener provides email_id)
    2. Batch classification (called in parallel for each email_id)
    
    This is the core classification node that does the actual work.
    """
    try:
        logger.info("Classifying single email...")

        client = state.mcp
        email_id = state.email_id  # The email ID being processed
        categories = state.categories
        
        # Fetch the email details
        async with client:
            raw_email = await client.read_resource(f"gmail://messages/{email_id}")
            email = message_from_string(raw_email[0].text)

        # logger.info(f"Fetched email: {email_id} - {email}")
            
        # Initialize llm
        llm = init_chat_model(
            model="gpt-4.1-mini", 
            model_provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        prompt = f"""Classify this email into one of these categories: {', '.join(categories)}

HERE IS THE EMAIL CONTENT:
{email.get_payload(decode=True).decode(errors='ignore')}

Respond with ONLY the category name, nothing else."""

        messages = [
            SystemMessage(content=prompt),
        ]
        
        # Generate email body
        response = llm.invoke(messages)
        # logger.info(f"Classification response: {response.content}")

        category = response.content
        
        # Return single classification result
        classification_result = {
            "email_id": email_id,
            "subject": email.get("Subject"),
            "from": email.get("From"),
            "category": category,
            "classified_at": datetime.now().isoformat()
        }
        
        return {
            "classification_results": [classification_result],
            "status": "classification_complete",
            "total_classified": 1
        }
        
    except Exception as e:
        return {
            "classification_results": [{
                "email_id": state.email_id,
                "error": str(e),
                "category": "error"
            }],
            "status": "error",
            "error": f"Failed to classify email: {e}"
        }


async def parallel_classify_node(state: EmailClassificationState) -> dict:
    """
    Orchestrate parallel classification of multiple emails.
    This node:
    1. Takes the list of email_ids from state
    2. Calls classify_single_email_node for each one IN PARALLEL
    3. Aggregates the results
    
    This is the batch orchestrator that parallelizes the single classification node.
    """
    try:
        logger.info(
            "Starting parallel classification of multiple emails..."
        )

        email_ids = state.email_ids
        
        if not email_ids:
            return {
                "status": "error",
                "error": "No email IDs to classify"
            }
        
        # Create a list of tasks - each one classifies a single email
        async def classify_one(email_id: str):
            # Create a temporary state for this single email
            single_state = EmailClassificationState(
                mode="single",
                email_id=email_id,
                categories=state.categories,
                mcp=state.mcp,
                apply_labels=True
            )
            # Call the single classification node
            return await classify_single_email_node(single_state)
        
        # Run all classifications in parallel
        tasks = [classify_one(email_id) for email_id in email_ids]
        classification_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for result in classification_results:
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "category": "error"
                })
            else:
                processed_results.append(result)
        
        return {
            "classification_results": processed_results,
            "status": "classification_complete",
            "total_classified": len(processed_results)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to classify emails in parallel: {e}"
        }


async def apply_labels_node(state: EmailClassificationState) -> dict:
    """
    Apply classification labels/categories to emails in Gmail.
    Works for both single and batch classification results.
    """
    try:
        logger.info("Applying labels to classified emails...")

        client = state.mcp
        results = state.classification_results
        
        labeled_count = 0
        errors = []

        for result in results:
            result = result['classification_results'][0]
            if result.get("category") and result.get("category") != "error":
                try:
                    async with client:
                        # Get label id by name (category)
                        raw = await client.call_tool("get_available_labels", {})
                        raw_text = raw.content[0].text
                        raw_json = json.loads(raw_text)
                        label_map = { lbl["name"]: lbl["id"] for lbl in raw_json["labels"] }
                        gmail_label_id = label_map[result["category"]]

                        # Apply label via MCP
                        await client.call_tool("add_label_to_message", {
                            "message_id": result["email_id"],
                            "label_id": gmail_label_id
                        })

                        labeled_count += 1
                except Exception as e:
                    errors.append({
                        "message_id": result["email_id"],
                        "error": str(e)
                    })
        
        return {
            "status": "labels_applied",
            "labeled_count": labeled_count,
            "label_errors": errors if errors else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to apply labels: {e}"
        }


def router_node(state: EmailClassificationState) -> str:
    """
    Route to appropriate workflow based on mode.
    - "single": Classify one email (from listener)
    - "batch": Classify multiple emails (fetch IDs first)
    """

    logger.info("Routing based on classification mode...")

    mode = state.mode if hasattr(state, 'mode') else state.get('mode')

    if mode == "single":
        return "classify_single"
    elif mode == "batch":
        return "fetch_email_ids"
    else:
        raise ValueError(f"Unknown mode: {state.mode}")

