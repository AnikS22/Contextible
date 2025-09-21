#!/usr/bin/env python3
"""
Direct test of context injection without proxy
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations.ollama import ollama_integration


async def test_direct_injection():
    """Test context injection directly."""
    print("🔍 Testing direct context injection...")
    
    # Test request
    test_request = {
        "model": "mistral:latest",
        "prompt": "What is my name and where do I work?",
        "stream": False
    }
    
    print(f"📤 Original request: {test_request}")
    
    # Test injection
    model_id = test_request["model"]
    enhanced_request = await ollama_integration.inject_context(test_request, model_id)
    
    print(f"📥 Enhanced request:")
    print(f"  Original prompt: {test_request['prompt']}")
    print(f"  Enhanced prompt: {enhanced_request.get('prompt', 'NO PROMPT FOUND')}")
    print(f"  Length change: {len(test_request['prompt'])} -> {len(enhanced_request.get('prompt', ''))}")
    
    if len(enhanced_request.get('prompt', '')) > len(test_request['prompt']):
        print("✅ Context injection is working!")
        return True
    else:
        print("❌ Context injection failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_direct_injection())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Direct injection test")
