import asyncio
from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
import os
from dotenv import load_dotenv
load_dotenv()

async def test_write_email():
    """Test 1: Write an email"""
    print("\n" + "="*70)
    print("TEST 1: Write Email via Orchestrator")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:9000"),
        )
        
        agent_card = await resolver.get_agent_card()
        print(f"✓ Connected to: {agent_card.name}")
        
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        # Test writing an email
        user_request = "Send an email to client@gmail.com with subject 'Test' saying hello"
        print(f"\nRequest: {user_request}")
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                message={
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': user_request}],
                    'messageId': uuid4().hex,
                },
                metadata={
                    'skill_id': 'orchestrate',
                    'input_params': {'request': user_request}
                }
            )
        )
        
        print("Sending to orchestrator...")
        response = await client.send_message(request)
        
        # Extract and print response
        result = response.model_dump()
        if 'result' in result and 'events' in result['result']:
            for event in result['result']['events']:
                if 'data' in event and 'text' in event['data']:
                    print(f"\n✓ Response:\n{event['data']['text']}")
        else:
            print(f"\nFull response: {result}")


async def test_draft_email():
    """Simple test for AI-generated draft email"""
    print("\n" + "="*70)
    print("TEST: Write Draft Email with AI Generation")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        # Connect to orchestrator
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:9000")
        )
        
        agent_card = await resolver.get_agent_card()
        print(f"✓ Connected to: {agent_card.name}")
        
        client = A2AClient(
            agent_card=agent_card,
            httpx_client=httpx_client
        )
        
        # Test 1: Draft email with clear parameters
        print("\n--- Test 1: Professional project update email ---")
        user_request = (
            "Write a professional email to client@gmail.com with subject 'Project Update'. "
            "Tell them the project is 80% complete and on schedule for delivery next week."
        )
        print(f"Request: {user_request}")
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                message={
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': user_request}],
                    'messageId': uuid4().hex,
                },
                metadata={
                    'skill_id': 'orchestrate',
                    'input_params': {'request': user_request}
                }
            )
        )
        
        print("\nSending to orchestrator (this will use AI to generate content)...")
        response = await client.send_message(request)
        
        # Extract and display response
        result = response.model_dump()
        if 'result' in result and 'events' in result['result']:
            for event in result['result']['events']:
                if 'data' in event and 'text' in event['data']:
                    print(f"\n✓ Response:")
                    print("="*70)
                    print(event['data']['text'])
                    print("="*70)
        else:
            print(f"\nFull response: {result}")


async def test_classify_emails():
    """Test 2: Classify emails"""
    print("\n" + "="*70)
    print("TEST 2: Classify Emails via Orchestrator")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:9000"),
        )
        
        agent_card = await resolver.get_agent_card()
        print(f"✓ Connected to: {agent_card.name}")
        
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        user_request = "Classify my emails from last 30 days into Work, Personal, and Newsletter"
        print(f"\nRequest: {user_request}")
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                message={
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': user_request}],
                    'messageId': uuid4().hex,
                },
                metadata={
                    'skill_id': 'orchestrate',
                    'input_params': {'request': user_request}
                }
            )
        )
        
        print("Sending to orchestrator...")
        response = await client.send_message(request)
        
        result = response.model_dump()
        if 'result' in result and 'events' in result['result']:
            for event in result['result']['events']:
                if 'data' in event and 'text' in event['data']:
                    print(f"\n✓ Response:\n{event['data']['text']}")
        else:
            print(f"\nFull response: {result}")


async def test_missing_params():
    """Test 3: Missing parameters (should ask for clarification)"""
    print("\n" + "="*70)
    print("TEST 3: Missing Parameters (Expect Clarification)")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:9000"),
        )
        
        agent_card = await resolver.get_agent_card()
        print(f"✓ Connected to: {agent_card.name}")
        
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        user_request = "Write an email about the project update"
        print(f"\nRequest: {user_request}")
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                message={
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': user_request}],
                    'messageId': uuid4().hex,
                },
                metadata={
                    'skill_id': 'orchestrate',
                    'input_params': {'request': user_request}
                }
            )
        )
        
        print("Sending to orchestrator...")
        response = await client.send_message(request)
        
        result = response.model_dump()
        if 'result' in result and 'events' in result['result']:
            for event in result['result']['events']:
                if 'data' in event and 'text' in event['data']:
                    print(f"\n✓ Response (should ask for recipient):\n{event['data']['text']}")
        else:
            print(f"\nFull response: {result}")


async def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("ORCHESTRATOR EMAIL TESTS")
    print("🚀"*35)
    print("\nPrerequisites:")
    print(f"  1. Email Agent running on {os.getenv('EMAIL_ASSISTANT_BASE_URL', 'http://localhost:9001')}")
    print(f"  2. Orchestrator running on {os.getenv('ORCHESTRATOR_BASE_URL', 'http://localhost:9000')}")
    print("\nStarting tests...")
    
    tests = [
        ("Write Email", test_write_email),
        ("Draft Email", test_draft_email),
        ("Classify Emails", test_classify_emails),
        ("Missing Parameters", test_missing_params),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            print(f"\n✅ {test_name} - PASSED")
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} - FAILED: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")


if __name__ == '__main__':
    asyncio.run(main())