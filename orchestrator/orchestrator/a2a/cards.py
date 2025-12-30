from a2a.types import AgentCard, AgentCapabilities
from orchestrator.a2a.skills import get_orchestrator_skills
from orchestrator.config import Config


# Public agent card - available to everyone
public_agent_card = AgentCard(

    name=Config.ORCHESTRATOR_NAME,
    description=Config.ORCHESTRATOR_DESCRIPTION,
    version=Config.ORCHESTRATOR_VERSION,
    url=f"http://{Config.HOST}:{Config.PORT}",

    capabilities=AgentCapabilities(
        streaming=False,
        supports_authenticated_extended_card=False,
    ),

    default_input_modes=["text"],
    default_output_modes=["text"],
    
    skills=get_orchestrator_skills()
)


# For now, orchestrator doesn't need an extended card
# All functionality is available in the public card
extended_agent_card = public_agent_card