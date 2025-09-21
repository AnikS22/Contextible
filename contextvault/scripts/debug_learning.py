#!/usr/bin/env python3
"""
Debug script to test the learning method directly
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.integrations.ollama import OllamaIntegration


async def test_learning_directly():
    """Test the learning method directly."""
    print("🔍 Testing Learning Method Directly")
    print("=" * 50)
    
    # Create integration instance
    integration = OllamaIntegration()
    
    # Mock request data
    request_data = {
        "model": "mistral:latest",
        "prompt": "Hi, my name is DebugUser and I work as a data scientist at Apple. I love Python programming.",
        "stream": False
    }
    
    # Mock response content (what we'd get from Ollama)
    response_content = b'{"model":"mistral:latest","created_at":"2025-09-20T21:30:00.000Z","response":"Hello DebugUser! It\'s great to meet you. As a data scientist at Apple who loves Python programming, you must be working on some exciting projects.","done":true}'
    
    model_id = "mistral:latest"
    session_id = "test_session_123"
    
    print(f"📝 Request data: {request_data}")
    print(f"📝 Response content: {response_content}")
    print(f"📝 Model ID: {model_id}")
    print(f"📝 Session ID: {session_id}")
    
    try:
        # Call the learning method directly
        await integration._learn_from_conversation(
            request_data,
            response_content,
            model_id,
            session_id
        )
        
        print("✅ Learning method completed without errors")
        
        # Check if context was actually saved
        from contextvault.models.context import ContextEntry
        from contextvault.database import get_db_context
        
        with get_db_context() as db:
            recent_entries = db.query(ContextEntry).filter(
                ContextEntry.entry_metadata.contains('auto_extracted')
            ).order_by(ContextEntry.created_at.desc()).limit(3).all()
        
        print(f"📊 Recent auto-extracted entries: {len(recent_entries)}")
        for entry in recent_entries:
            print(f"  - {entry.content}")
            print(f"    Type: {entry.context_type}, Source: {entry.source}")
        
    except Exception as e:
        print(f"❌ Learning method failed: {e}")
        import traceback
        traceback.print_exc()


async def test_conversation_logger():
    """Test conversation logger directly."""
    print("\n📝 Testing Conversation Logger Directly")
    print("=" * 50)
    
    from contextvault.services.conversation_logger import conversation_logger
    
    # Start conversation
    conv_id = conversation_logger.start_conversation("test_model", {"debug": True})
    print(f"✅ Started conversation: {conv_id}")
    
    # Log messages
    conversation_logger.log_user_message(conv_id, "Hi, my name is LoggerTest and I work at Google.")
    conversation_logger.log_assistant_message(conv_id, "Hello LoggerTest! Great to meet you.")
    
    # Get conversation
    conversation = conversation_logger.get_conversation(conv_id)
    if conversation:
        print(f"✅ Retrieved conversation with {len(conversation.messages)} messages")
        for msg in conversation.messages:
            print(f"  - {msg.role}: {msg.content[:50]}...")
    else:
        print("❌ Failed to retrieve conversation")
    
    # Get stats
    stats = conversation_logger.get_conversation_stats()
    print(f"📊 Stats: {stats}")


async def test_full_extraction_pipeline():
    """Test the full extraction pipeline."""
    print("\n🔍 Testing Full Extraction Pipeline")
    print("=" * 50)
    
    from contextvault.services.conversation_logger import conversation_logger
    from contextvault.services.context_extractor import context_extractor
    from contextvault.services.deduplication import context_deduplicator
    from contextvault.services.validation import context_validator
    from contextvault.models.context import ContextEntry
    from contextvault.database import get_db_context
    
    # Create test conversation
    conv_id = conversation_logger.start_conversation("test_model")
    conversation_logger.log_user_message(conv_id, "Hi, my name is PipelineTest and I'm a software engineer at Microsoft. I love working with Python and machine learning.")
    conversation_logger.log_assistant_message(conv_id, "Hello PipelineTest! It's great to meet another software engineer at Microsoft who loves Python.")
    
    # Get conversation
    conversation = conversation_logger.get_conversation(conv_id)
    if not conversation:
        print("❌ Failed to get conversation")
        return
    
    print(f"✅ Got conversation with {len(conversation.messages)} messages")
    
    # Extract context
    extracted = context_extractor.extract_from_conversation(conv_id, conversation)
    print(f"✅ Extracted {len(extracted)} context entries")
    
    for i, context in enumerate(extracted, 1):
        print(f"  {i}. {context.content}")
        print(f"     Type: {context.context_type}, Confidence: {context.confidence}")
    
    # Get existing contexts for deduplication
    with get_db_context() as db:
        existing_contexts = db.query(ContextEntry).all()
    
    # Deduplicate
    deduplicated = context_deduplicator.deduplicate_extracted_context(extracted, existing_contexts)
    print(f"✅ After deduplication: {len(deduplicated)} context entries")
    
    # Validate
    validation_results = context_validator.validate_context_batch(deduplicated)
    print(f"✅ Validation results: {len(validation_results)}")
    
    # Show validation details
    for i, (context, validation_result) in enumerate(zip(deduplicated, validation_results), 1):
        print(f"  {i}. Status: {validation_result.status.value}, Confidence: {validation_result.confidence:.2f}")
        if validation_result.issues:
            print(f"     Issues: {validation_result.issues}")
        if validation_result.suggestions:
            print(f"     Suggestions: {validation_result.suggestions}")
    
    # Save to database
    saved_count = 0
    with get_db_context() as db:
        for context, validation_result in zip(deduplicated, validation_results):
            if validation_result.status.value in ['valid', 'needs_review', 'uncertain']:
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
        db.commit()
    
    print(f"✅ Saved {saved_count} context entries to database")


async def main():
    """Run all debug tests."""
    print("🐛 Debug Learning System")
    print("=" * 60)
    
    try:
        await test_conversation_logger()
        await test_full_extraction_pipeline()
        await test_learning_directly()
        
        print("\n" + "=" * 60)
        print("✅ All debug tests completed")
        
    except Exception as e:
        print(f"\n❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
