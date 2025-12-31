from a2a.types import AgentCard, AgentCapabilities
from .skills import write_email_skill, classify_emails_skill

from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:9001")

# Public Agent Card (unauthenticated)
# Shows basic capabilities without requiring user authentication
public_agent_card = AgentCard(
    name='Email Assistant',
    description=(
        'AI-powered email assistant for composing, sending, and organizing emails. '
        'Features AI draft generation with tone control and intelligent email classification.'
    ),
    url=BASE_URL,  
    version='1.0.0',
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(
        streaming=False  # Set to True if you implement streaming
    ),
    skills=[write_email_skill],  # Public card shows basic skill
    supports_authenticated_extended_card=True,  # Indicates more skills available after auth
)

# Extended Agent Card (authenticated)
# Shows full capabilities after user authentication
extended_agent_card = AgentCard(
    name='Email Assistant (Full Access)',
    description=(
        'Full-featured AI email assistant with complete access to email composition, '
        'sending, and advanced inbox organization through intelligent classification. '
        'Includes batch processing and parallel email categorization.'
    ),
    url=BASE_URL, 
    version='1.0.0',
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(
        streaming=False
    ),
    skills=[write_email_skill, classify_emails_skill],  # All skills available
    supports_authenticated_extended_card=False,  # Already at highest level
)