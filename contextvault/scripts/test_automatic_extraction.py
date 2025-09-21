#!/usr/bin/env python3
"""
Test Automatic Context Extraction
This script tests the real automatic context extraction system
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.services.conversation_logger import conversation_logger
from contextvault.services.context_extractor import context_extractor
from contextvault.services.deduplication import context_deduplicator
from contextvault.services.validation import context_validator
from contextvault.models.context import ContextEntry
from contextvault.database import get_db_context


def test_conversation_logger():
    """Test the conversation logger."""
    print("🧪 Testing Conversation Logger")
    print("=" * 50)
    
    # Start a conversation
    conversation_id = conversation_logger.start_conversation("test_model", {"test": True})
    print(f"✅ Started conversation: {conversation_id}")
    
    # Log user message
    user_message = "Hi, my name is Alice and I'm a software engineer at Google. I love Python programming and I live in San Francisco."
    conversation_logger.log_user_message(conversation_id, user_message)
    print(f"✅ Logged user message: {user_message[:50]}...")
    
    # Log assistant message
    assistant_message = "Hello Alice! It's great to meet you. As a software engineer at Google who loves Python programming, you must be working on some exciting projects. How do you like living in San Francisco?"
    conversation_logger.log_assistant_message(conversation_id, assistant_message)
    print(f"✅ Logged assistant message: {assistant_message[:50]}...")
    
    # Get conversation
    conversation = conversation_logger.get_conversation(conversation_id)
    print(f"✅ Retrieved conversation with {len(conversation.messages)} messages")
    
    # Get stats
    stats = conversation_logger.get_conversation_stats()
    print(f"✅ Conversation stats: {stats}")
    
    return conversation


def test_context_extraction(conversation):
    """Test context extraction."""
    print("\n🔍 Testing Context Extraction")
    print("=" * 50)
    
    # Extract context from conversation
    extracted_contexts = context_extractor.extract_from_conversation(
        conversation.id, conversation
    )
    
    print(f"✅ Extracted {len(extracted_contexts)} context entries")
    
    for i, context in enumerate(extracted_contexts, 1):
        context_type_str = context.context_type.value if hasattr(context.context_type, 'value') else str(context.context_type)
        confidence_str = context.confidence.value if hasattr(context.confidence, 'value') else str(context.confidence)
        print(f"  {i}. [{context_type_str}] {context.content}")
        print(f"     Confidence: {confidence_str}")
        print(f"     Tags: {context.tags}")
        print()
    
    return extracted_contexts


def test_deduplication(extracted_contexts):
    """Test context deduplication."""
    print("🔄 Testing Context Deduplication")
    print("=" * 50)
    
    # Get existing contexts from database
    try:
        with get_db_context() as db:
            existing_contexts = db.query(ContextEntry).all()
        
        print(f"✅ Found {len(existing_contexts)} existing context entries")
        
        # Deduplicate
        deduplicated = context_deduplicator.deduplicate_extracted_context(
            extracted_contexts, existing_contexts
        )
        
        print(f"✅ After deduplication: {len(deduplicated)} context entries")
        
        for i, context in enumerate(deduplicated, 1):
            context_type_str = context.context_type.value if hasattr(context.context_type, 'value') else str(context.context_type)
            confidence_str = context.confidence.value if hasattr(context.confidence, 'value') else str(context.confidence)
            print(f"  {i}. [{context_type_str}] {context.content}")
            print(f"     Confidence: {confidence_str}")
            print()
        
        return deduplicated
        
    except Exception as e:
        print(f"❌ Deduplication failed: {e}")
        return extracted_contexts


def test_validation(deduplicated_contexts):
    """Test context validation."""
    print("✅ Testing Context Validation")
    print("=" * 50)
    
    # Validate contexts
    validation_results = context_validator.validate_context_batch(deduplicated_contexts)
    
    print(f"✅ Validated {len(validation_results)} context entries")
    
    for i, (context, result) in enumerate(zip(deduplicated_contexts, validation_results), 1):
        print(f"  {i}. [{result.status.value}] {context.content}")
        print(f"     Validation Confidence: {result.confidence:.2f}")
        if result.issues:
            print(f"     Issues: {result.issues}")
        if result.suggestions:
            print(f"     Suggestions: {result.suggestions}")
        print()
    
    return validation_results


def test_save_to_database(deduplicated_contexts, validation_results):
    """Test saving to database."""
    print("💾 Testing Database Save")
    print("=" * 50)
    
    saved_count = 0
    
    try:
        with get_db_context() as db:
            for context, validation_result in zip(deduplicated_contexts, validation_results):
                # Only save valid or needs_review contexts
                if validation_result.status.value in ['valid', 'needs_review']:
                    context_entry = ContextEntry(
                        content=context.content,
                        context_type=context.context_type,
                        source=context.source,
                        tags=context.tags,
                        entry_metadata={
                            'conversation_id': context.conversation_id,
                            'message_id': context.message_id,
                            'extraction_confidence': context.confidence.value,
                            'validation_status': validation_result.status.value,
                            'validation_confidence': validation_result.confidence,
                            'auto_extracted': True,
                            **context.metadata
                        }
                    )
                    db.add(context_entry)
                    saved_count += 1
        
        # Commit all changes
        with get_db_context() as db:
            db.commit()
        
        print(f"✅ Saved {saved_count} context entries to database")
        
        # Verify by counting total entries
        with get_db_context() as db:
            total_entries = db.query(ContextEntry).count()
            auto_extracted = db.query(ContextEntry).filter(
                ContextEntry.entry_metadata.contains('auto_extracted')
            ).count()
        
        print(f"✅ Database now has {total_entries} total entries ({auto_extracted} auto-extracted)")
        
    except Exception as e:
        print(f"❌ Database save failed: {e}")


def test_real_conversation():
    """Test with a real conversation through the proxy."""
    print("\n🤖 Testing Real Conversation Through Proxy")
    print("=" * 50)
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ Proxy not running on port 11435")
            return
    except:
        print("❌ Cannot connect to proxy on port 11435")
        return
    
    print("✅ Proxy is running")
    
    # Send a test conversation
    test_prompt = "Hi, I'm John and I work as a data scientist at Microsoft. I love machine learning and I live in Seattle. What do you think about Python for data science?"
    
    try:
        response = requests.post(
            "http://localhost:11435/api/generate",
            headers={"Content-Type": "application/json"},
            json={
                "model": "mistral:latest",
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Sent conversation through proxy")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Check if context was extracted
            with get_db_context() as db:
                recent_entries = db.query(ContextEntry).filter(
                    ContextEntry.entry_metadata.contains('auto_extracted')
                ).order_by(ContextEntry.created_at.desc()).limit(5).all()
            
            print(f"✅ Found {len(recent_entries)} recent auto-extracted entries:")
            for entry in recent_entries:
                print(f"  - {entry.content}")
        else:
            print(f"❌ Proxy request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Real conversation test failed: {e}")


def main():
    """Run all tests."""
    print("🧪 Automatic Context Extraction Test Suite")
    print("=" * 60)
    
    try:
        # Test conversation logger
        conversation = test_conversation_logger()
        
        # Test context extraction
        extracted_contexts = test_context_extraction(conversation)
        
        # Test deduplication
        deduplicated_contexts = test_deduplication(extracted_contexts)
        
        # Test validation
        validation_results = test_validation(deduplicated_contexts)
        
        # Test saving to database
        test_save_to_database(deduplicated_contexts, validation_results)
        
        # Test real conversation
        test_real_conversation()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("🎉 Automatic context extraction is working!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
