from a2a.types import AgentSkill
from typing import List


def get_orchestrator_skills() -> List[AgentSkill]:
    """
    Define the skills that the orchestrator exposes.
    
    The orchestrator has a single skill that handles all user requests
    by parsing intent and routing to appropriate email assistant skills.
    
    Returns:
        List of Skill objects
    """
    skills = [
        AgentSkill(
            id="orchestrate",
            name="Orchestrate Email Operations",
            description=(
                "Intelligent orchestration of email operations. "
                "Understands natural language requests and routes them to appropriate email skills. "
                "Handles: writing emails, classifying emails, and other email-related tasks. "
                "Automatically extracts parameters from user requests and asks for missing information."
            ),
            tags=["orchestration", "email", "nlp", "routing"],
            # input_modes=[
            #     "Natural language description of what you want to do with emails. "
            #     "Examples: "
            #     "'Send an email to john@example.com about the meeting tomorrow', "
            #     "'Classify my emails from last week into Work and Personal categories', "
            #     "'Write a professional email to the team about project status'"
            # ],
            # output_modes=[
            #     "Execution result including status, any generated content, and confirmation of action taken."
            # ],
            requires_auth=False,
            parameters=[
                {
                    "name": "request",
                    "type": "string",
                    "description": "Natural language description of the email operation",
                    "required": True
                }
            ]
        )
    ]
    
    return skills