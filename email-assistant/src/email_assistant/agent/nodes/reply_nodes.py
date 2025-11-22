from email_assistant.core.schemas import EmailState
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv
import os

load_dotenv() 

def direct_send_node(state: EmailState) -> dict:
    """
    Directly send email using provided text without generation.
    
    Args:
        state: Current email state
        
    Returns:
        Updated state after sending
    """
    try:
        # Use the provided text as-is
        body = state.text
        
        return {
            **state.model_dump(),
            "generated_body": body,
            "status": "sent_directly"
        }
    
    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to perform direct_send_email: {str(e)}"
        }
    
async def send_draft_node(state: EmailState) -> dict:
    """
    Async node: send email using MCP async client.
    """
    try:
        body = state.generated_body or state.text

        # Get MCP client from state
        client = state.mcp

        async with client:
            # Debug: list tools
            tools = await client.list_tools()
            print("Tools:", tools)

            # Call your MCP tool (name must match server-side tool)
            result = await client.call_tool("compose_email", {
                "to": state.to,
                "subject": state.subject,
                "body": body,
                "cc": state.cc,
                "bcc": state.bcc,
            })

            print("send_email tool result:", result)

        return {
            **state.model_dump(),
            "status": "sent_successfully",
            "mcp_result": result
        }

    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to send email: {e}"
        }

def generate_draft_node(state: EmailState) -> dict:
    """
    Generate email draft using LLM based on instructions and tone.
    
    Args:
        state: Current email state
        
    Returns:
        Updated state with generated body
    """
    try:
        # Initialize llm
        llm = init_chat_model(
            model="gpt-4.1-mini", 
            model_provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        # Create prompt for email generation
        system_prompt = f"""You are an expert email writer. Generate a professional email based on the user's instructions.

Tone: {state.tone}

Guidelines:
- Be clear and concise
- Match the specified tone ({state.tone})
- Ensure proper email etiquette
- Do not include subject line or recipient details (only body content)
- Keep it professional yet natural
"""
        
        user_prompt = f"""Write an email body based on these instructions:

{state.text}

Remember to match the {state.tone} tone."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Generate email body
        response = llm.invoke(messages)
        generated_body = response.content
        
        return {
            **state.model_dump(),
            "generated_body": generated_body,
            "status": "draft_generated"
        }
    
    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to generate draft: {str(e)}"
        }

async def send_email_node(state: EmailState) -> dict:
    """
    Async node: send email using MCP async client.
    """
    try:
        body = state.generated_body or state.text

        # Get MCP client from state
        client = state.mcp

        async with client:
            # Debug: list tools
            tools = await client.list_tools()
            print("Tools:", tools)

            # Call your MCP tool (name must match server-side tool)
            result = await client.call_tool("send_email", {
                "to": state.to,
                "subject": state.subject,
                "body": body,
                "cc": state.cc,
                "bcc": state.bcc,
            })

            print("send_email tool result:", result)

        return {
            **state.model_dump(),
            "status": "sent_successfully",
            "mcp_result": result
        }

    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to send email: {e}"
        }

def router_node(state: EmailState) -> Literal["generate_draft", "direct_send"]:
    """
    Router node that decides whether to generate a draft or send directly.
    
    Args:
        state: Current email state
        
    Returns:
        Next node to execute
    """
    if state.should_generate:
        return "generate_draft"
    return "direct_send"