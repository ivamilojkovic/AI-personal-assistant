from email_assistant.core.schemas import EmailState
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv() 

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
