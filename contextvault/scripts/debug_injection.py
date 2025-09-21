#!/usr/bin/env python3
"""
Debug context injection process step by step
"""

import sys
import json
import asyncio
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations.ollama import OllamaIntegration
from contextvault.database import get_db_context
from contextvault.services.context_retrieval import ContextRetrievalService

async def debug_injection():
    """Debug the context injection process step by step"""
    
    print("🔍 DEBUGGING CONTEXT INJECTION")
    print("=" * 50)
    
    # Step 1: Test context retrieval directly
    print("\n📋 Step 1: Testing Context Retrieval")
    with get_db_context() as db:
        service = ContextRetrievalService(db_session=db)
        result = service.get_context_for_prompt('mistral:latest', 'What pets do I have?')
        
        print(f"✅ Context entries found: {len(result.get('context_entries', []))}")
        print(f"✅ Formatted context length: {len(result.get('formatted_context', ''))}")
        print(f"✅ Total length: {result.get('total_length', 0)}")
        
        if result.get('formatted_context'):
            print(f"✅ Formatted context preview: {result['formatted_context'][:200]}...")
    
    # Step 2: Test the integration's inject_context method
    print("\n🔧 Step 2: Testing Context Injection")
    integration = OllamaIntegration()
    
    # Create a test request
    test_request = {
        "model": "mistral:latest",
        "prompt": "What pets do I have?"
    }
    
    print(f"📝 Original prompt: {test_request['prompt']}")
    
    # Test the injection
    modified_request = await integration.inject_context(
        request_data=test_request,
        model_id="mistral:latest"
    )
    
    print(f"📝 Modified prompt length: {len(modified_request.get('prompt', ''))}")
    print(f"📝 Original prompt length: {len(test_request.get('prompt', ''))}")
    
    if len(modified_request.get('prompt', '')) > len(test_request.get('prompt', '')):
        print("✅ Context was injected!")
        print(f"📝 Modified prompt preview: {modified_request.get('prompt', '')[:300]}...")
    else:
        print("❌ Context was NOT injected!")
    
    # Step 3: Test the full proxy request
    print("\n🌐 Step 3: Testing Full Proxy Request")
    
    request_body = json.dumps(test_request).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    
    result = await integration.proxy_request(
        path='/api/generate',
        method='POST',
        headers=headers,
        body=request_body,
        inject_context=True
    )
    
    print(f"✅ Proxy result status: {result.get('status_code', 'unknown')}")
    
    if result.get('status_code') == 200:
        # Parse the response to see if context was used
        content = result.get('content', '')
        print(f"📝 Raw response length: {len(content)}")
        print(f"📝 Raw response preview: {content[:300]}...")
        
        # Try to extract the full response from streaming data
        try:
            # This is a streaming response, so we need to collect all the response parts
            full_response = ""
            lines = content.decode('utf-8').split('\n')
            
            for line in lines:
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            full_response += chunk['response']
                    except json.JSONDecodeError:
                        continue
            
            if full_response:
                print(f"📝 AI response length: {len(full_response)}")
                print(f"📝 AI response: {full_response}")
                
                # Check if the AI mentioned any of our context
                context_keywords = ['Luna', 'Pixel', 'cats', 'San Francisco', 'Tesla']
                found_keywords = [kw for kw in context_keywords if kw.lower() in full_response.lower()]
                
                if found_keywords:
                    print(f"✅ AI mentioned context: {found_keywords}")
                else:
                    print("❌ AI did NOT mention any context keywords")
            else:
                print("❌ Could not extract response from streaming data")
        except Exception as e:
            print(f"❌ Error parsing streaming response: {e}")
    else:
        print(f"❌ Proxy request failed: {result}")

if __name__ == "__main__":
    asyncio.run(debug_injection())
