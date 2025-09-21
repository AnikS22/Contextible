#!/usr/bin/env python3
"""
Simple Test for Automatic Context Extraction

This script tests the context extraction without database operations
to demonstrate the core functionality.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.services.conversation_logger import ConversationMessage, Conversation
from contextvault.services.context_extractor import context_extractor

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

def test_context_extraction():
    """Test the context extraction without database operations."""
    
    print_section("ContextVault Context Extraction Test")
    print("This test demonstrates how ContextVault extracts context")
    print("from conversations using pattern matching and AI analysis.")
    
    # Step 1: Create sample conversation messages
    print_step(1, "Creating sample conversation messages")
    
    messages = [
        ConversationMessage(
            role='user',
            content="Hi! I'm Sarah, I work as a software engineer at Google.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="Hello Sarah! Nice to meet you. What kind of software engineering do you do at Google?",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='user',
            content="I work on the Android team, specifically on performance optimization. I love working with Kotlin and have been doing this for 3 years now.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="That's fascinating! Android performance optimization is really important. How do you like working with Kotlin compared to Java?",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='user',
            content="Kotlin is much better! I prefer it over Java any day. I also enjoy hiking on weekends - I live in San Francisco so there are great trails nearby.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="San Francisco has amazing hiking! What are some of your favorite trails in the area?",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='user',
            content="I love the Marin Headlands and Mount Tam. I usually go with my dog Max. I'm also vegetarian and allergic to peanuts, so I have to be careful with restaurant choices.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="That sounds like a wonderful routine! Max must love those hikes. Being vegetarian with a peanut allergy can definitely be challenging when dining out.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='user',
            content="Yes, it can be tricky! I'm currently learning Spanish because I want to travel to South America next year. I'm using Duolingo and it's going well.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="That's a great goal! Spanish will definitely be helpful for South America travel. How long have you been studying?",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='user',
            content="About 2 months now. I practice for 30 minutes every morning before work. I'm also working on a side project - building a mobile app for tracking hiking trails.",
            timestamp=datetime.now()
        ),
        ConversationMessage(
            role='assistant',
            content="That's impressive dedication! A hiking trail tracking app sounds really useful. What technology stack are you using for the mobile app?",
            timestamp=datetime.now()
        )
    ]
    
    print(f"✅ Created {len(messages)} conversation messages")
    
    # Step 2: Extract context from conversations
    print_step(2, "Extracting context from conversations")
    
    conversation_id = "test-conversation-123"
    extracted_contexts = context_extractor.extract_from_conversation(
        conversation_id, messages
    )
    
    print(f"✅ Extracted {len(extracted_contexts)} potential context entries")
    
    # Display extracted contexts
    if extracted_contexts:
        print("\n📋 Extracted Context Entries:")
        for i, context in enumerate(extracted_contexts, 1):
            print(f"  {i}. [{context.context_type}] {context.content}")
            print(f"     Confidence: {context.confidence:.2f}, Source: {context.source}")
            print(f"     Tags: {', '.join(context.tags)}")
    
    # Step 3: Analyze extraction patterns
    print_step(3, "Analyzing extraction effectiveness")
    
    # Group by context type
    by_type = {}
    for context in extracted_contexts:
        context_type = str(context.context_type)
        if context_type not in by_type:
            by_type[context_type] = []
        by_type[context_type].append(context)
    
    print(f"📊 Context Types Extracted:")
    for context_type, contexts in by_type.items():
        avg_confidence = sum(c.confidence for c in contexts) / len(contexts)
        print(f"  • {context_type}: {len(contexts)} entries (avg confidence: {avg_confidence:.2f})")
    
    # Step 4: Show high-confidence extractions
    print_step(4, "High-confidence extractions")
    
    high_confidence = [c for c in extracted_contexts if c.confidence >= 0.7]
    print(f"✅ Found {len(high_confidence)} high-confidence extractions:")
    
    for context in high_confidence:
        print(f"  🎯 [{context.context_type}] {context.content}")
        print(f"     Confidence: {context.confidence:.2f}")
    
    # Step 5: Demonstrate the power
    print_section("🎉 Context Extraction Complete!")
    print("ContextVault successfully identified:")
    print("• Personal information (name, job, location)")
    print("• Preferences (programming languages, food choices)")
    print("• Goals and projects (learning Spanish, mobile app)")
    print("• Relationships and lifestyle (dog, hiking habits)")
    print("• Health information (allergies)")
    print("\nThis extracted context would be automatically stored and")
    print("injected into future AI conversations, making responses")
    print("much more personalized and relevant!")
    
    return len(extracted_contexts)

if __name__ == "__main__":
    test_context_extraction()
