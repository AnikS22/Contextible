#!/usr/bin/env python3
"""Debug script to test conversation learning."""

import sys
import asyncio
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations.ollama import ollama_integration
from contextvault.services.conversation_learning import conversation_learning_service

async def test_conversation_learning():
    """Test conversation learning directly."""
    print("🧪 Testing Conversation Learning Directly")
    print("=" * 50)
    
    # Test the conversation learning service directly
    test_prompt = "I am working on a new AI project called SmartCode that helps developers write better code."
    test_response = "That sounds like an exciting project! SmartCode could be a valuable tool for developers."
    
    print(f"📝 Test Prompt: {test_prompt}")
    print(f"🤖 Test Response: {test_response}")
    
    try:
        # Test direct learning
        await conversation_learning_service.learn_from_conversation(
            user_prompt=test_prompt,
            ai_response=test_response,
            model_id="test_model",
            session_id="test_session",
            user_id=None
        )
        print("✅ Direct conversation learning succeeded")
    except Exception as e:
        print(f"❌ Direct conversation learning failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the integration's learning method
    print("\n🔧 Testing Integration Learning Method")
    print("-" * 30)
    
    try:
        request_data = {
            "model": "test_model",
            "prompt": test_prompt
        }
        
        # Mock response content
        response_content = json.dumps({"response": test_response}).encode('utf-8')
        
        await ollama_integration._learn_from_conversation(
            request_data=request_data,
            response_content=response_content,
            model_id="test_model",
            session_id="test_session"
        )
        print("✅ Integration conversation learning succeeded")
    except Exception as e:
        print(f"❌ Integration conversation learning failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversation_learning())
