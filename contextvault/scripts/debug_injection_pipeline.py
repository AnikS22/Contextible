#!/usr/bin/env python3
"""
Debug Context Injection Pipeline
Comprehensive debugging to trace exactly what's happening in the injection process
"""

import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context, init_database
from contextvault.models.context import ContextEntry, ContextSource, ContextCategory
from contextvault.integrations.ollama import ollama_integration
from contextvault.services.intelligent_retrieval import IntelligentContextRetrieval
from contextvault.services.templates import template_manager, format_context_with_template


def clear_and_add_test_context():
    """Clear database and add known test context."""
    print("🧹 Clearing database and adding test context...")
    
    init_database()
    
    with get_db_context() as db:
        # Clear all existing context
        db.query(ContextEntry).delete()
        db.commit()
        
        # Add specific test context
        test_contexts = [
            {
                "content": "I am Alex, a software engineer in Portland who loves coffee and pizza. I work at TechCorp and my favorite programming language is Python.",
                "context_type": "personal_info",
                "context_source": ContextSource.MANUAL,
                "context_category": ContextCategory.PERSONAL_INFO,
                "confidence_score": 1.0,
                "tags": ["alex", "engineer", "portland", "coffee", "pizza", "python"]
            },
            {
                "content": "I prefer working from home and I hate morning meetings. I love hiking on weekends and I'm allergic to cats.",
                "context_type": "preference", 
                "context_source": ContextSource.MANUAL,
                "context_category": ContextCategory.PREFERENCES,
                "confidence_score": 1.0,
                "tags": ["work", "meetings", "hiking", "allergies"]
            }
        ]
        
        for ctx_data in test_contexts:
            entry = ContextEntry(**ctx_data)
            db.add(entry)
        
        db.commit()
        print(f"✅ Added {len(test_contexts)} test context entries")


def test_database_access():
    """Test database access and show current context."""
    print("\n🔍 Testing database access...")
    
    try:
        with get_db_context() as db:
            entries = db.query(ContextEntry).all()
            print(f"✅ Database accessible: {len(entries)} entries found")
            
            for i, entry in enumerate(entries[:3]):
                print(f"  {i+1}. {entry.content[:80]}...")
                print(f"     Type: {entry.context_type}, Category: {entry.context_category}")
                
        return len(entries) > 0
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_context_retrieval():
    """Test context retrieval service."""
    print("\n🔍 Testing context retrieval...")
    
    try:
        retrieval_service = IntelligentContextRetrieval()
        
        # Test retrieval (not async)
        results = retrieval_service.retrieve_context(
            query="What do you know about my preferences and where I live?",
            user_id=None,
            max_results=5
        )
        
        print(f"✅ Context retrieval working: {len(results)} results")
        for i, result in enumerate(results):
            content = result.context.get("content", str(result.context)) if isinstance(result.context, dict) else result.context.content
            print(f"  {i+1}. Score: {result.total_score:.3f} - {content[:60]}...")
        
        return len(results) > 0
    except Exception as e:
        print(f"❌ Context retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_system():
    """Test template system."""
    print("\n🔍 Testing template system...")
    
    try:
        # Get current template
        current_template = template_manager.get_template()
        print(f"✅ Current template: {current_template.name if current_template else 'None'}")
        
        # Test formatting
        context_entries = ["I am Alex from Portland", "I love coffee"]
        original_prompt = "What do you know about me?"
        
        formatted = format_context_with_template(
            context_entries=context_entries,
            user_prompt=original_prompt,
            template_name=None
        )
        
        print(f"✅ Template formatting working")
        print(f"  Original: {original_prompt}")
        print(f"  Enhanced: {formatted[:200]}...")
        
        return len(formatted) > len(original_prompt)
    except Exception as e:
        print(f"❌ Template system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_injection_pipeline():
    """Test the complete injection pipeline."""
    print("\n🔍 Testing full injection pipeline...")
    
    try:
        # Create test request
        test_request = {
            "model": "mistral:latest",
            "prompt": "What do you know about my food preferences and location?",
            "stream": False
        }
        
        print(f"📤 Original request: {test_request['prompt']}")
        
        # Test injection
        model_id = test_request["model"]
        enhanced_request = await ollama_integration.inject_context(test_request, model_id)
        
        print(f"📥 Enhanced request prompt length: {len(enhanced_request.get('prompt', ''))}")
        print(f"📥 Enhanced prompt preview: {enhanced_request.get('prompt', '')[:300]}...")
        
        # Check if prompt was actually enhanced
        original_prompt = test_request["prompt"]
        enhanced_prompt = enhanced_request.get("prompt", "")
        
        if len(enhanced_prompt) > len(original_prompt):
            print("✅ Context injection appears to be working")
            return True
        else:
            print("❌ Context injection failed - prompt not enhanced")
            return False
            
    except Exception as e:
        print(f"❌ Full injection pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_proxy_integration():
    """Test proxy integration end-to-end."""
    print("\n🔍 Testing proxy integration...")
    
    try:
        import httpx
        
        # Test request through proxy
        test_data = {
            "model": "mistral:latest", 
            "prompt": "What is my name and where do I work?",
            "stream": False
        }
        
        print(f"📤 Sending request to proxy: {test_data['prompt']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11435/api/generate",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                print(f"📥 AI Response: {ai_response[:200]}...")
                
                # Check if response mentions our test context
                response_lower = ai_response.lower()
                test_indicators = ["alex", "portland", "coffee", "pizza", "python", "techcorp"]
                found_indicators = [indicator for indicator in test_indicators if indicator in response_lower]
                
                print(f"🎯 Found context indicators: {found_indicators}")
                
                if found_indicators:
                    print("✅ Context injection is working through proxy!")
                    return True
                else:
                    print("❌ Context injection not working - AI response is generic")
                    return False
            else:
                print(f"❌ Proxy request failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Proxy integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive debugging tests."""
    print("🚀 Context Injection Pipeline Debugging")
    print("=" * 50)
    
    # Step 1: Setup test data
    clear_and_add_test_context()
    
    # Step 2: Test database
    db_ok = test_database_access()
    if not db_ok:
        print("❌ Database test failed - stopping")
        return
    
    # Step 3: Test context retrieval
    retrieval_ok = test_context_retrieval()
    if not retrieval_ok:
        print("❌ Context retrieval test failed - stopping")
        return
    
    # Step 4: Test template system
    template_ok = test_template_system()
    if not template_ok:
        print("❌ Template system test failed - stopping")
        return
    
    # Step 5: Test injection pipeline
    injection_ok = asyncio.run(test_full_injection_pipeline())
    if not injection_ok:
        print("❌ Injection pipeline test failed")
    
    # Step 6: Test proxy integration
    proxy_ok = asyncio.run(test_proxy_integration())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEBUGGING SUMMARY")
    print("=" * 50)
    print(f"Database Access: {'✅' if db_ok else '❌'}")
    print(f"Context Retrieval: {'✅' if retrieval_ok else '❌'}")
    print(f"Template System: {'✅' if template_ok else '❌'}")
    print(f"Injection Pipeline: {'✅' if injection_ok else '❌'}")
    print(f"Proxy Integration: {'✅' if proxy_ok else '❌'}")
    
    if all([db_ok, retrieval_ok, template_ok, injection_ok, proxy_ok]):
        print("\n🎉 ALL TESTS PASSED - Context injection is working!")
    else:
        print("\n🚨 SOME TESTS FAILED - Context injection has issues")


if __name__ == "__main__":
    main()
