#!/usr/bin/env python3
"""
Final Verification Test for Context Injection
Tests the complete pipeline to ensure context injection is working end-to-end
"""

import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context, init_database
from contextvault.models.context import ContextEntry, ContextSource, ContextCategory


def setup_test_data():
    """Setup comprehensive test data."""
    print("🧹 Setting up test data...")
    
    init_database()
    
    with get_db_context() as db:
        # Clear existing context
        db.query(ContextEntry).delete()
        db.commit()
        
        # Add comprehensive test context
        test_contexts = [
            {
                "content": "I am Alex, a software engineer in Portland who loves coffee and pizza. I work at TechCorp and my favorite programming language is Python.",
                "context_type": "personal_info",
                "context_source": ContextSource.MANUAL,
                "context_category": ContextCategory.PERSONAL_INFO,
                "confidence_score": 1.0,
                "tags": ["alex", "engineer", "portland", "coffee", "pizza", "python", "techcorp"]
            },
            {
                "content": "I prefer working from home and I hate morning meetings. I love hiking on weekends and I'm allergic to cats.",
                "context_type": "preference", 
                "context_source": ContextSource.MANUAL,
                "context_category": ContextCategory.PREFERENCES,
                "confidence_score": 1.0,
                "tags": ["work", "meetings", "hiking", "allergies", "cats"]
            },
            {
                "content": "I have two cats named Luna and Pixel. Luna is black and white, Pixel is orange.",
                "context_type": "personal_info",
                "context_source": ContextSource.MANUAL,
                "context_category": ContextCategory.PERSONAL_INFO,
                "confidence_score": 1.0,
                "tags": ["pets", "cats", "luna", "pixel"]
            }
        ]
        
        for ctx_data in test_contexts:
            entry = ContextEntry(**ctx_data)
            db.add(entry)
        
        db.commit()
        print(f"✅ Added {len(test_contexts)} test context entries")


async def test_context_injection():
    """Test context injection through the proxy."""
    print("\n🔍 Testing context injection through proxy...")
    
    test_cases = [
        {
            "prompt": "What is my name and where do I work?",
            "expected_indicators": ["alex", "techcorp", "engineer"]
        },
        {
            "prompt": "What do I like to eat and drink?",
            "expected_indicators": ["coffee", "pizza"]
        },
        {
            "prompt": "What pets do I have?",
            "expected_indicators": ["luna", "pixel", "cats"]
        },
        {
            "prompt": "What are my work preferences?",
            "expected_indicators": ["working from home", "morning meetings"]
        }
    ]
    
    import httpx
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['prompt']}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11435/api/generate",
                    json={
                        "model": "mistral:latest",
                        "prompt": test_case["prompt"],
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("response", "").lower()
                    
                    # Check for expected indicators
                    found_indicators = []
                    for indicator in test_case["expected_indicators"]:
                        if indicator.lower() in ai_response:
                            found_indicators.append(indicator)
                    
                    print(f"  📥 AI Response: {result.get('response', '')[:100]}...")
                    print(f"  🎯 Found indicators: {found_indicators}")
                    print(f"  ✅ Expected: {test_case['expected_indicators']}")
                    
                    if found_indicators:
                        print(f"  ✅ PASSED: Found {len(found_indicators)}/{len(test_case['expected_indicators'])} expected indicators")
                    else:
                        print(f"  ❌ FAILED: No expected indicators found")
                        all_tests_passed = False
                else:
                    print(f"  ❌ FAILED: HTTP {response.status_code}")
                    all_tests_passed = False
                    
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            all_tests_passed = False
    
    return all_tests_passed


def test_database_access():
    """Test database access and show context entries."""
    print("\n🔍 Testing database access...")
    
    try:
        with get_db_context() as db:
            entries = db.query(ContextEntry).all()
            print(f"✅ Database accessible: {len(entries)} entries found")
            
            for i, entry in enumerate(entries, 1):
                print(f"  {i}. {entry.content[:80]}...")
                print(f"     Type: {entry.context_type}, Category: {entry.context_category}")
                
        return len(entries) > 0
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def main():
    """Run comprehensive verification tests."""
    print("🚀 Final Verification Test for Context Injection")
    print("=" * 60)
    
    # Setup test data
    setup_test_data()
    
    # Test database
    db_ok = test_database_access()
    if not db_ok:
        print("❌ Database test failed - stopping")
        return False
    
    # Test context injection
    injection_ok = await test_context_injection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Database Access: {'✅' if db_ok else '❌'}")
    print(f"Context Injection: {'✅' if injection_ok else '❌'}")
    
    if db_ok and injection_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Context injection is working perfectly!")
        print("✅ AI responses are personalized with stored context!")
        print("✅ The ContextVault system is fully functional!")
        return True
    else:
        print("\n🚨 SOME TESTS FAILED!")
        print("❌ Context injection needs attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
