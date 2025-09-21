#!/usr/bin/env python3
"""
Debug ContextRetrievalService to see why it's not finding context
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context
from contextvault.services.context_retrieval import ContextRetrievalService


def debug_context_retrieval():
    """Debug the ContextRetrievalService."""
    print("🔍 Debugging ContextRetrievalService...")
    
    try:
        with get_db_context() as db:
            service = ContextRetrievalService(db_session=db)
            
            print(f"📤 Testing with model: mistral:latest")
            print(f"📤 Testing with prompt: What is my name and where do I work?")
            
            # Test the exact method called by Ollama integration
            result = service.get_context_for_prompt(
                model_id="mistral:latest",
                user_prompt="What is my name and where do I work?",
                max_context_length=1000
            )
            
            print(f"📥 Result keys: {list(result.keys())}")
            print(f"📥 Context entries: {len(result.get('context_entries', []))}")
            print(f"📥 Total length: {result.get('total_length', 0)}")
            print(f"📥 Formatted context length: {len(result.get('formatted_context', ''))}")
            
            if result.get('context_entries'):
                print(f"📥 First entry: {result['context_entries'][0]}")
            else:
                print("📥 No context entries found")
                
                # Let's check what's in the database directly
                from contextvault.models.context import ContextEntry
                all_entries = db.query(ContextEntry).all()
                print(f"📥 Total entries in database: {len(all_entries)}")
                
                for i, entry in enumerate(all_entries[:3]):
                    print(f"  {i+1}. {entry.content[:60]}...")
                    print(f"     Type: {entry.context_type}, Category: {entry.context_category}")
                    print(f"     Source: {entry.context_source}")
            
            return len(result.get('context_entries', [])) > 0
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_context_retrieval()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: ContextRetrievalService debug")