import asyncio
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
)

from email_assistant.core.logger import Logger
logger = Logger.get_logger(__name__)

from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

async def test_write_email_no_auth():
    """Test write_email skill without authentication"""
    logger.info("=" * 70)
    logger.info("TEST 1: Write Email (No Auth)")
    logger.info("=" * 70)
    
    base_url = BASE_URL
    
    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        # Fetch public agent card
        logger.info(f'Fetching public agent card from: {base_url}/.well-known/agent.json')
        public_card = await resolver.get_agent_card()
        logger.info('Successfully fetched public agent card:')
        logger.info(f'Agent: {public_card.name}')
        logger.info(f'Skills: {[skill.id for skill in public_card.skills]}')
        
        # Initialize A2AClient
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=public_card
        )
        logger.info('A2AClient initialized.')
        
        # Create message for write_email skill
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': 'Send an email to iva97.ja@gmail.com with subject "Test" and body "Hello from A2A client"'
                    }
                ],
                'messageId': uuid4().hex,
            },
            'metadata': {
                'skill_id': 'write_email',
                'input_params': {
                    'to': 'iva97.ja@gmail.com',
                    'subject': 'Test Email from A2A Client',
                    'text': 'Hello from A2A client',
                    'tone': 'professional',
                    'should_generate': False
                }
            }
        }
        
        # Construct and send request
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        logger.info('Sending message...')
        response = await client.send_message(request)
        
        # Print response
        logger.info('Response received:')
        print(response.model_dump(mode='json', exclude_none=True))


async def test_write_email_with_generation():
    """Test write_email skill with AI generation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Write Email with AI Generation")
    logger.info("=" * 70)
    
    base_url = BASE_URL
    
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        public_card = await resolver.get_agent_card()
        
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=public_card
        )
        
        # Create message with AI generation
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': 'Write a professional email to the team about project completion'
                    }
                ],
                'messageId': uuid4().hex,
            },
            'metadata': {
                'skill_id': 'write_email',
                'input_params': {
                    'to': 'iva97.ja@gmail.com',
                    'subject': 'Project Completion',
                    'text': 'Tell the team that the project is 95% complete, we finished all core features, and are now doing final testing',
                    'tone': 'professional',
                    'should_generate': True
                }
            }
        }
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        logger.info('Sending message with AI generation...')
        response = await client.send_message(request)
        
        logger.info('Response received:')
        print(response.model_dump(mode='json', exclude_none=True))


async def test_classify_emails_with_auth():
    """Test classify_emails skill with authentication"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Classify Emails (With Auth)")
    logger.info("=" * 70)
    
    base_url = BASE_URL
    auth_token = 'test-token-123'

    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        # Fetch public card first
        public_card = await resolver.get_agent_card()
        logger.info(f'Public card skills: {[skill.id for skill in public_card.skills]}')
        
        # Try to fetch extended card if supported
        final_card = public_card
        if public_card.supports_authenticated_extended_card:
            try:
                logger.info('Fetching extended agent card with authentication...')
                auth_headers = {'Authorization': f'Bearer {auth_token}'}
                
                # Try the standard extended card path
                extended_card = await resolver.get_agent_card(
                    relative_card_path='/.well-known/agent.json',
                    http_kwargs={'headers': auth_headers}
                )
                
                logger.info('Successfully fetched extended agent card:')
                logger.info(f'Extended card skills: {[skill.id for skill in extended_card.skills]}')
                final_card = extended_card
            except Exception as e:
                logger.warning(f'Failed to fetch extended card: {e}')
                logger.info('Continuing with public card...')
        
        # Initialize client with the final card
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=final_card
        )
        
        # Create message for classify_emails skill
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': 'Classify my emails from the last 7 days'
                    }
                ],
                'messageId': uuid4().hex,
            },
            "metadata": {
                "skill_id": "classify_emails",
                'input_params': {
                    "days_back": 7,
                    "categories": ["Work", "Personal", "Newsletter"]
                }
            }
        }
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload), 
        )
        
        logger.info('Sending classification request...')
        response = await client.send_message(request)
        
        print(">>> EMAIL CLASSIFICATION RESULT <<<")
        print(response)

        logger.info('Response received:')
        print(response.model_dump(mode='json', exclude_none=True))

async def run_all_tests():
    """Run all A2A client tests"""
    logger.info("🚀" * 35)
    logger.info("EMAIL ASSISTANT A2A CLIENT - TEST SUITE")
    logger.info("🚀" * 35)
    
    tests = [
        ("Write Email (No Auth)", test_write_email_no_auth),
        ("Write Email with Generation", test_write_email_with_generation),
        ("Classify Emails (With Auth)", test_classify_emails_with_auth),
    ]
    
    for test_name, test_func in tests:
        try:
            await test_func()
            logger.info(f"✅ {test_name} completed\n")
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {str(e)}", exc_info=True)
    
    logger.info("=" * 70)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 70)


if __name__ == '__main__':
    asyncio.run(run_all_tests())