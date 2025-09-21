#!/usr/bin/env python3
"""
Test Automatic Context Extraction

This script demonstrates ContextVault's ability to automatically extract
and store context from AI conversations without manual intervention.
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.services.conversation_logger import conversation_logger
from contextvault.services.context_extractor import context_extractor
from contextvault.services.deduplication import context_deduplicator
from contextvault.services.validation import context_validator
from contextvault.database import get_db_context
from contextvault.models import ContextEntry

def print_section(title, content=""):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")
    if content:
        print(content)

def print_step(step_num, description):
    """Print a numbered step."""
    print(f"\n📝 Step {step_num}: {description}")

async def test_automatic_context_extraction():
    """Test the complete automatic context extraction pipeline."""
    
    print_section("ContextVault Automatic Context Extraction Test")
    print("This test demonstrates how ContextVault automatically learns")
    print("from your conversations and builds a persistent memory.")
    
    # Step 1: Simulate conversations
    print_step(1, "Simulating realistic AI conversations")
    
    # Create a conversation session
    conversation_id = conversation_logger.start_conversation("mistral:latest")
    print(f"✅ Started conversation: {conversation_id}")
    
    # Sample conversations that should trigger context extraction
    conversations = [
        {
            "user": "Hi! I'm Sarah, I work as a software engineer at Google.",
            "ai": "Hello Sarah! Nice to meet you. What kind of software engineering do you do at Google?"
        },
        {
            "user": "I work on the Android team, specifically on performance optimization. I love working with Kotlin and have been doing this for 3 years now.",
            "ai": "That's fascinating! Android performance optimization is really important. How do you like working with Kotlin compared to Java?"
        },
        {
            "user": "Kotlin is much better! I prefer it over Java any day. I also enjoy hiking on weekends - I live in San Francisco so there are great trails nearby.",
            "ai": "San Francisco has amazing hiking! What are some of your favorite trails in the area?"
        },
        {
            "user": "I love the Marin Headlands and Mount Tam. I usually go with my dog Max. I'm also vegetarian and allergic to peanuts, so I have to be careful with restaurant choices.",
            "ai": "That sounds like a wonderful routine! Max must love those hikes. Being vegetarian with a peanut allergy can definitely be challenging when dining out."
        },
        {
            "user": "Yes, it can be tricky! I'm currently learning Spanish because I want to travel to South America next year. I'm using Duolingo and it's going well.",
            "ai": "That's a great goal! Spanish will definitely be helpful for South America travel. How long have you been studying?"
        },
        {
            "user": "About 2 months now. I practice for 30 minutes every morning before work. I'm also working on a side project - building a mobile app for tracking hiking trails.",
            "ai": "That's impressive dedication! A hiking trail tracking app sounds really useful. What technology stack are you using for the mobile app?"
        }
    ]
    
    # Log all conversations
    for i, conv in enumerate(conversations, 1):
        conversation_logger.log_user_message(conversation_id, conv["user"])
        conversation_logger.log_assistant_message(conversation_id, conv["ai"])
        print(f"  📝 Logged conversation {i}/6")
        time.sleep(0.1)  # Small delay for realistic timing
    
    # End the conversation
    conversation = conversation_logger.end_conversation(conversation_id)
    print(f"✅ Ended conversation with {len(conversation.messages)} messages")
    
    # Step 2: Extract context
    print_step(2, "Extracting context from conversations")
    
    extracted_contexts = context_extractor.extract_from_conversation(
        conversation_id, conversation.messages
    )
    
    print(f"✅ Extracted {len(extracted_contexts)} potential context entries")
    
    # Display extracted contexts
    if extracted_contexts:
        print("\n📋 Extracted Context Entries:")
        for i, context in enumerate(extracted_contexts, 1):
            print(f"  {i}. [{context.context_type}] {context.content}")
            print(f"     Confidence: {context.confidence:.2f}, Source: {context.source}")
    
    # Step 3: Get existing contexts for deduplication
    print_step(3, "Checking for existing contexts")
    
    with get_db_context() as db:
        existing_contexts = db.query(ContextEntry).all()
    
    print(f"✅ Found {len(existing_contexts)} existing context entries")
    
    # Step 4: Deduplicate
    print_step(4, "Deduplicating extracted contexts")
    
    deduplicated_contexts = context_deduplicator.deduplicate_extracted_context(
        extracted_contexts, existing_contexts
    )
    
    print(f"✅ After deduplication: {len(deduplicated_contexts)} unique contexts")
    
    if len(deduplicated_contexts) < len(extracted_contexts):
        removed_count = len(extracted_contexts) - len(deduplicated_contexts)
        print(f"   🗑️ Removed {removed_count} duplicate entries")
    
    # Step 5: Validate
    print_step(5, "Validating extracted contexts")
    
    validation_results = context_validator.validate_context_batch(deduplicated_contexts)
    
    valid_count = sum(1 for r in validation_results if r.status.value == 'valid')
    review_count = sum(1 for r in validation_results if r.status.value == 'needs_review')
    invalid_count = sum(1 for r in validation_results if r.status.value == 'invalid')
    
    print(f"✅ Validation Results:")
    print(f"   🟢 Valid: {valid_count}")
    print(f"   🟡 Needs Review: {review_count}")
    print(f"   🔴 Invalid: {invalid_count}")
    
    # Display validation details
    if deduplicated_contexts:
        print("\n📊 Validation Details:")
        for i, (context, result) in enumerate(zip(deduplicated_contexts, validation_results), 1):
            status_emoji = {
                'valid': '🟢',
                'needs_review': '🟡',
                'invalid': '🔴'
            }.get(result.status.value, '⚪')
            
            print(f"  {i}. {status_emoji} [{context.context_type}] {context.content[:50]}...")
            print(f"     Confidence: {result.confidence:.2f}, Issues: {len(result.issues)}")
            if result.issues:
                print(f"     Issues: {', '.join(result.issues[:2])}")
    
    # Step 6: Save valid contexts
    print_step(6, "Saving validated contexts to database")
    
    saved_count = 0
    for context, result in zip(deduplicated_contexts, validation_results):
        # Only save valid contexts and those that need review
        if result.status.value in ['valid', 'needs_review']:
            try:
                with get_db_context() as db:
                    context_entry = ContextEntry(
                        content=context.content,
                        context_type=context.context_type,
                        source=context.source,
                        tags=', '.join(context.tags),
                        metadata={
                            'conversation_id': context.conversation_id,
                            'extraction_confidence': context.confidence,
                            'validation_status': result.status.value,
                            'validation_confidence': result.confidence,
                            'auto_extracted': True,
                            'test_extraction': True,
                            **context.metadata
                        }
                    )
                    db.add(context_entry)
                    db.commit()
                    saved_count += 1
                    
            except Exception as e:
                print(f"   ❌ Failed to save context: {e}")
    
    print(f"✅ Successfully saved {saved_count} context entries")
    
    # Step 7: Show final results
    print_step(7, "Final Results")
    
    # Get updated context count
    with get_db_context() as db:
        total_contexts = db.query(ContextEntry).count()
        auto_extracted = db.query(ContextEntry).filter(
            ContextEntry.metadata.contains('auto_extracted')
        ).count()
    
    print(f"📊 Database Statistics:")
    print(f"   📝 Total context entries: {total_contexts}")
    print(f"   🤖 Auto-extracted entries: {auto_extracted}")
    print(f"   👤 Manual entries: {total_contexts - auto_extracted}")
    
    # Show conversation stats
    stats = conversation_logger.get_conversation_stats()
    print(f"\n💬 Conversation Statistics:")
    print(f"   📈 Total conversations: {stats['total_conversations']}")
    print(f"   🔄 Active conversations: {stats['active_conversations']}")
    
    # Step 8: Demonstrate the power
    print_section("🎉 Automatic Context Extraction Complete!")
    print("ContextVault has automatically learned:")
    print("• Personal information (name, job, location)")
    print("• Preferences (programming languages, food choices)")
    print("• Goals and projects (learning Spanish, mobile app)")
    print("• Relationships and lifestyle (dog, hiking habits)")
    print("• Health information (allergies)")
    print("\nThis context will now be automatically injected into future AI conversations,")
    print("making the AI responses much more personalized and relevant!")
    
    return saved_count

if __name__ == "__main__":
    asyncio.run(test_automatic_context_extraction())
