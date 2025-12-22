from a2a.types import AgentSkill

# Skill 1: Write and Send Email
write_email_skill = AgentSkill(
    id='write_email',
    name='Write and Send Email',
    description=(
        'Compose and send emails with optional AI-powered draft generation. '
        'Can either send text directly or generate professional email content '
        'from instructions. Supports different tones (professional, casual, formal, friendly).'
    ),
    tags=['email', 'compose', 'send', 'draft', 'generate'],
    examples=[
        'Send an email to john@example.com about tomorrow\'s meeting',
        'Write a professional email to the client about project delays',
        'Draft an email thanking the team for their hard work',
        'Send a casual email to my colleague about lunch plans',
    ],
)

# Skill 2: Classify Emails
classify_emails_skill = AgentSkill(
    id='classify_emails',
    name='Classify and Label Emails',
    description=(
        'Automatically classify emails in your inbox into predefined categories '
        'and apply Gmail labels. Processes emails in batch mode with parallel '
        'classification. Useful for organizing inbox and managing email flow.'
    ),
    tags=['email', 'classify', 'label', 'organize', 'inbox', 'categorize'],
    examples=[
        'Classify my emails from the last 7 days into Work, Personal, and Newsletter',
        'Label emails from this week as Work or Personal',
        'Classify and organize my unread emails',
    ],
)

# List of all skills
ALL_SKILLS = [write_email_skill, classify_emails_skill]