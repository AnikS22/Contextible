#!/usr/bin/env python3
"""
Debug script to test context injection step by step.
This will help us identify exactly where the pipeline is failing.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations import ollama_integration
from contextvault.services import vault_service
from contextvault.database import get_db_context


async def debug_context_injection():
    """Debug the context injection pipeline step by step."""
    
    print("🔍 CONTEXT INJECTION DEBUG")
    print("=" * 50)
    
    # Step 1: Check if we have any context entries
    print("\n1. Checking existing context entries...")
    try:
        with get_db_context() as db:
            from contextvault.models import ContextEntry
            entries = db.query(ContextEntry).all()
            print(f"   Found {len(entries)} context entries in database")
            
            if entries:
                for i, entry in enumerate(entries[:3]):
                    print(f"   {i+1}. [{entry.context_type}] {entry.content[:50]}...")
            else:
                print("   ❌ No context entries found!")
                return
                
    except Exception as e:
        print(f"   ❌ Error checking context: {e}")
        return
    
    # Step 2: Test context retrieval
    print("\n2. Testing context retrieval...")
    try:
        from contextvault.services.context_retrieval import ContextRetrievalService
        
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            test_prompt = "What do you know about me?"
            
            context_result = retrieval_service.get_context_for_prompt(
                model_id="mistral:latest",
                user_prompt=test_prompt,
                max_context_length=1000,
            )
            
            print(f"   Context retrieval result: {context_result}")
            
            if context_result.get("error"):
                print(f"   ❌ Context retrieval failed: {context_result['error']}")
                return
                
            context_entries = context_result.get("context_entries", [])
            print(f"   Retrieved {len(context_entries)} context entries")
            
            if not context_entries:
                print("   ❌ No context entries retrieved!")
                return
                
    except Exception as e:
        print(f"   ❌ Error in context retrieval: {e}")
        return
    
    # Step 3: Test template formatting
    print("\n3. Testing template formatting...")
    try:
        from contextvault.services.templates import template_manager
        
        # Extract content from context entries
        context_strings = []
        for entry in context_entries:
            if isinstance(entry, dict):
                content = entry.get('content', str(entry))
            else:
                content = entry.content if hasattr(entry, 'content') else str(entry)
            context_strings.append(content)
        
        print(f"   Context strings to format: {len(context_strings)}")
        for i, ctx in enumerate(context_strings[:2]):
            print(f"   {i+1}. {ctx[:50]}...")
        
        # Test template formatting
        formatted_prompt = template_manager.format_context(
            context_entries=context_strings,
            user_prompt=test_prompt,
            template_name="forced_reference"  # Use the strongest template
        )
        
        print(f"   ✅ Template formatting successful")
        print(f"   Original prompt: {test_prompt}")
        print(f"   Enhanced prompt length: {len(formatted_prompt)} chars")
        print(f"   Enhanced prompt preview:")
        print("   " + "-" * 40)
        print("   " + formatted_prompt[:200] + "...")
        print("   " + "-" * 40)
        
    except Exception as e:
        print(f"   ❌ Error in template formatting: {e}")
        return
    
    # Step 4: Test full context injection
    print("\n4. Testing full context injection...")
    try:
        test_request = {
            "model": "mistral:latest",
            "prompt": test_prompt,
            "stream": False
        }
        
        print(f"   Original request: {json.dumps(test_request, indent=2)}")
        
        # Call inject_context directly
        enhanced_request = await ollama_integration.inject_context(
            request_data=test_request,
            model_id="mistral:latest",
            session=None
        )
        
        print(f"   ✅ Context injection successful")
        print(f"   Enhanced request prompt:")
        print("   " + "-" * 40)
        print("   " + enhanced_request.get("prompt", "NO PROMPT")[:200] + "...")
        print("   " + "-" * 40)
        
        # Check if prompt was actually modified
        if enhanced_request.get("prompt") == test_prompt:
            print("   ❌ WARNING: Prompt was not modified!")
            print("   The context injection didn't work!")
            return
        else:
            print("   ✅ Prompt was successfully modified with context")
            
    except Exception as e:
        print(f"   ❌ Error in context injection: {e}")
        return
    
    # Step 5: Test actual Ollama request
    print("\n5. Testing actual Ollama request...")
    try:
        import httpx
        
        # Make request to Ollama directly with enhanced prompt
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=enhanced_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                ai_response = response_data.get("response", "")
                
                print(f"   ✅ Ollama request successful")
                print(f"   AI Response:")
                print("   " + "-" * 40)
                print("   " + ai_response[:300] + "...")
                print("   " + "-" * 40)
                
                # Check if AI response mentions context
                context_mentioned = False
                for ctx in context_strings:
                    if any(word.lower() in ai_response.lower() for word in ctx.split()[:3]):
                        context_mentioned = True
                        break
                
                if context_mentioned:
                    print("   ✅ SUCCESS: AI response mentions context!")
                else:
                    print("   ❌ WARNING: AI response doesn't seem to mention context")
                    
            else:
                print(f"   ❌ Ollama request failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Error in Ollama request: {e}")
        return
    
    print("\n🎯 DEBUG COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(debug_context_injection())
