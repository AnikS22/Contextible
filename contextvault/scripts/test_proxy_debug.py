#!/usr/bin/env python3
"""
Test proxy with detailed debugging
"""

import sys
import asyncio
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations.ollama import ollama_integration


async def test_proxy_debug():
    """Test proxy request with detailed debugging."""
    print("🔍 Testing proxy request with debugging...")
    
    # Test request
    test_data = {
        "model": "mistral:latest",
        "prompt": "What is my name?",
        "stream": False
    }
    
    print(f"📤 Test request: {test_data}")
    
    # Call proxy_request directly
    try:
        result = await ollama_integration.proxy_request(
            path="/api/generate",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(test_data).encode('utf-8'),
            inject_context=True
        )
        
        print(f"📥 Proxy result status: {result['status_code']}")
        
        if result['status_code'] == 200:
            response_data = json.loads(result['content'].decode('utf-8'))
            ai_response = response_data.get('response', '')
            print(f"📥 AI Response: {ai_response[:200]}...")
            
            # Check if response mentions context
            response_lower = ai_response.lower()
            context_indicators = ["alex", "portland", "coffee", "pizza", "prefer", "working", "hiking"]
            found_indicators = [indicator for indicator in context_indicators if indicator in response_lower]
            
            print(f"🎯 Found context indicators: {found_indicators}")
            
            if found_indicators:
                print("✅ Context injection is working through proxy!")
                return True
            else:
                print("❌ Context injection not working - AI response is generic")
                return False
        else:
            print(f"❌ Proxy request failed: HTTP {result['status_code']}")
            return False
            
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_proxy_debug())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Proxy debug test")
