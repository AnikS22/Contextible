#!/usr/bin/env python3
"""
Test the ContextRetrievalService that the Ollama integration actually uses
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context
from contextvault.services.context_retrieval import ContextRetrievalService


def test_context_retrieval_service():
    """Test the actual service used by Ollama integration."""
    print("🔍 Testing ContextRetrievalService...")
    
    try:
        with get_db_context() as db:
            service = ContextRetrievalService(db_session=db)
            
            # Test the exact method called by Ollama integration
            result = service.get_context_for_prompt(
                model_id="mistral:latest",
                user_prompt="What is my name and where do I work?",
                max_context_length=1000
            )
            
            print(f"✅ Service call successful")
            print(f"Result keys: {list(result.keys())}")
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return False
            
            context_entries = result.get("context_entries", [])
            print(f"✅ Found {len(context_entries)} context entries")
            
            for i, entry in enumerate(context_entries):
                if hasattr(entry, 'content'):
                    content = entry.content
                elif isinstance(entry, dict):
                    content = entry.get('content', str(entry))
                else:
                    content = str(entry)
                print(f"  {i+1}. {content[:80]}...")
            
            return len(context_entries) > 0
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_context_retrieval_service()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: ContextRetrievalService test")
