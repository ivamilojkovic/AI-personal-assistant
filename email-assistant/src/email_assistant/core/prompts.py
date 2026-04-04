SUBSCRIPTION_CLASSIFICATION_PROMPT = """You are classifying emails to detect newsletters and subscription services.
Given ONLY the sender address and subject line, determine if this is a newsletter, marketing email, or subscription service.
Do NOT assume anything beyond what the sender and subject tell you.

Sender: {from_field}
Subject: {subject}

Respond with JSON only, no explanation:
{{"is_subscription": true or false, "confidence": 0 to 100, "name": "readable display name of the sender or service"}}"""
