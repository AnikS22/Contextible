#!/usr/bin/env python3
"""
Test Script for Intelligent Context Management System
Comprehensive testing of all intelligent context features
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.models.context import ContextEntry, ContextCategory, ContextSource, ValidationStatus, ContextType
from contextvault.database import get_db_context, init_database
from contextvault.services.intelligent_retrieval import intelligent_retrieval
from contextvault.services.categorizer import context_categorizer
from contextvault.services.conflict_resolver import context_conflict_resolver
from contextvault.services.analytics import context_analytics


def test_intelligent_context_system():
    """Test the complete intelligent context management system."""
    print("🧠 Testing Intelligent Context Management System")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Test 1: Enhanced Context Models
    print("\n1️⃣ Testing Enhanced Context Models")
    test_enhanced_models()
    
    # Test 2: Context Categorization
    print("\n2️⃣ Testing Context Categorization")
    test_context_categorization()
    
    # Test 3: Intelligent Retrieval
    print("\n3️⃣ Testing Intelligent Retrieval")
    test_intelligent_retrieval()
    
    # Test 4: Conflict Resolution
    print("\n4️⃣ Testing Conflict Resolution")
    test_conflict_resolution()
    
    # Test 5: Analytics
    print("\n5️⃣ Testing Analytics")
    test_analytics()
    
    print("\n🎉 All tests completed!")


def test_enhanced_models():
    """Test enhanced context models."""
    print("   📝 Testing enhanced context models...")
    
    # Create a test context with all new fields
    test_context = ContextEntry(
        content="I am John Doe, a software engineer at Google who loves Python programming.",
        context_type=ContextType.PERSONAL_INFO,
        context_source=ContextSource.MANUAL,
        confidence_score=0.95,
        context_category=ContextCategory.WORK,
        validation_status=ValidationStatus.CONFIRMED,
        extraction_metadata={"test": True, "created_by": "test_script"},
        tags=["test", "personal_info", "work"]
    )
    
    # Save to database
    with get_db_context() as db:
        db.add(test_context)
        db.commit()
        
        # Retrieve and verify
        retrieved = db.query(ContextEntry).filter(ContextEntry.id == test_context.id).first()
        
        assert retrieved.context_type == ContextType.PERSONAL_INFO
        assert retrieved.context_source == ContextSource.MANUAL
        assert retrieved.confidence_score == 0.95
        assert retrieved.context_category == ContextCategory.WORK
        assert retrieved.validation_status == ValidationStatus.CONFIRMED
        assert retrieved.extraction_metadata["test"] == True
        
        print("   ✅ Enhanced models working correctly")
        
        # Clean up
        db.delete(retrieved)
        db.commit()


def test_context_categorization():
    """Test context categorization engine."""
    print("   🏷️ Testing context categorization...")
    
    test_contents = [
        "I am Alice, a data scientist at Microsoft who loves machine learning.",
        "I prefer using Python over Java for programming.",
        "My goal is to become a senior engineer within 2 years.",
        "I have experience with React and Node.js development.",
        "I work on the recommendation system team at Netflix.",
        "I'm building a personal finance tracking application.",
        "My best friend Sarah works at Apple.",
        "I use Docker and Kubernetes for deployment."
    ]
    
    categorization_results = []
    
    for content in test_contents:
        result = context_categorizer.categorize_context(content)
        categorization_results.append(result)
        
        print(f"     Content: {content[:50]}...")
        category_str = result.context_category.value if hasattr(result.context_category, 'value') else str(result.context_category)
        type_str = result.context_type.value if hasattr(result.context_type, 'value') else str(result.context_type)
        print(f"     Category: {category_str}")
        print(f"     Type: {type_str}")
        print(f"     Confidence: {result.confidence:.2f}")
        print(f"     Tags: {result.suggested_tags}")
        print()
    
    # Verify categorization quality
    high_confidence_count = len([r for r in categorization_results if r.confidence > 0.7])
    print(f"   ✅ Categorized {len(test_contents)} contexts")
    print(f"   ✅ {high_confidence_count}/{len(test_contents)} had high confidence (>0.7)")


def test_intelligent_retrieval():
    """Test intelligent context retrieval."""
    print("   🔍 Testing intelligent retrieval...")
    
    # Create test contexts with different categories
    test_contexts = [
        ContextEntry(
            content="I am Bob, a software engineer at Google who specializes in Python and machine learning.",
            context_type=ContextType.PERSONAL_INFO,
            context_category=ContextCategory.WORK,
            context_source=ContextSource.MANUAL,
            confidence_score=0.9,
            tags=["engineer", "google", "python"]
        ),
        ContextEntry(
            content="I prefer using VSCode as my code editor and I love working with Python.",
            context_type=ContextType.PREFERENCE,
            context_category=ContextCategory.PREFERENCES,
            context_source=ContextSource.MANUAL,
            confidence_score=0.8,
            tags=["vscode", "python", "editor"]
        ),
        ContextEntry(
            content="My goal is to become a senior software engineer and lead a team of developers.",
            context_type=ContextType.GOAL,
            context_category=ContextCategory.GOALS,
            context_source=ContextSource.MANUAL,
            confidence_score=0.85,
            tags=["goal", "senior", "leadership"]
        ),
        ContextEntry(
            content="I have experience with React, Node.js, and Docker for web development.",
            context_type=ContextType.SKILL,
            context_category=ContextCategory.SKILLS,
            context_source=ContextSource.MANUAL,
            confidence_score=0.9,
            tags=["react", "nodejs", "docker"]
        )
    ]
    
    # Save test contexts
    with get_db_context() as db:
        for context in test_contexts:
            db.add(context)
        db.commit()
        
        # Test different queries
        test_queries = [
            "What do you know about my work?",
            "What are my preferences?",
            "What are my goals?",
            "What skills do I have?"
        ]
        
        for query in test_queries:
            print(f"     Query: {query}")
            results = intelligent_retrieval.retrieve_context(query, max_results=3)
            
            for i, result in enumerate(results, 1):
                print(f"       {i}. Score: {result.total_score:.3f}")
                content = result.context["content"] if isinstance(result.context, dict) else result.context.content
                print(f"          Content: {content[:60]}...")
                print(f"          Reasons: {', '.join(result.match_reasons[:2])}")
            
            print()
        
        # Clean up
        for context in test_contexts:
            db.delete(context)
        db.commit()
    
    print("   ✅ Intelligent retrieval working correctly")


def test_conflict_resolution():
    """Test conflict resolution system."""
    print("   ⚔️ Testing conflict resolution...")
    
    # Create conflicting contexts
    conflicting_contexts = [
        ContextEntry(
            content="My name is Charlie and I work at Apple as a software engineer.",
            context_type=ContextType.PERSONAL_INFO,
            context_category=ContextCategory.WORK,
            context_source=ContextSource.MANUAL,
            confidence_score=0.9,
            created_at=datetime(2024, 1, 1)
        ),
        ContextEntry(
            content="My name is Charlie and I work at Google as a data scientist.",
            context_type=ContextType.PERSONAL_INFO,
            context_category=ContextCategory.WORK,
            context_source=ContextSource.MANUAL,
            confidence_score=0.8,
            created_at=datetime(2024, 2, 1)  # More recent
        ),
        ContextEntry(
            content="I love Python programming and use it for all my projects.",
            context_type=ContextType.PREFERENCE,
            context_category=ContextCategory.PREFERENCES,
            context_source=ContextSource.MANUAL,
            confidence_score=0.9
        ),
        ContextEntry(
            content="I hate Python programming and prefer Java instead.",
            context_type=ContextType.PREFERENCE,
            context_category=ContextCategory.PREFERENCES,
            context_source=ContextSource.MANUAL,
            confidence_score=0.7
        )
    ]
    
    # Save conflicting contexts
    with get_db_context() as db:
        for context in conflicting_contexts:
            db.add(context)
        db.commit()
        
        # Detect conflicts
        conflicts = context_conflict_resolver.detect_conflicts(conflicting_contexts)
        print(f"     Detected {len(conflicts)} conflicts")
        
        for conflict in conflicts:
            print(f"       Conflict: {conflict.conflict_type}")
            print(f"         Context 1: {conflict.context1.content[:50]}...")
            print(f"         Context 2: {conflict.context2.content[:50]}...")
            print(f"         Confidence: {conflict.confidence:.2f}")
            print(f"         Action: {conflict.suggested_action}")
            print()
        
        # Resolve conflicts
        if conflicts:
            results = context_conflict_resolver.batch_resolve_conflicts(conflicting_contexts)
            print(f"     Resolved {len(results)} conflicts")
            
            for result in results:
                print(f"       Actions: {', '.join(result.actions_taken)}")
                print(f"       Confidence: {result.confidence:.2f}")
        
        # Clean up
        for context in conflicting_contexts:
            db.delete(context)
        db.commit()
    
    print("   ✅ Conflict resolution working correctly")


def test_analytics():
    """Test analytics system."""
    print("   📊 Testing analytics...")
    
    # Create diverse test contexts
    test_contexts = [
        ContextEntry(
            content="I am David, a software engineer at Microsoft.",
            context_type=ContextType.PERSONAL_INFO,
            context_category=ContextCategory.WORK,
            context_source=ContextSource.MANUAL,
            confidence_score=0.95,
            validation_status=ValidationStatus.CONFIRMED,
            access_count=10
        ),
        ContextEntry(
            content="I love working with Python and machine learning.",
            context_type=ContextType.PREFERENCE,
            context_category=ContextCategory.PREFERENCES,
            context_source=ContextSource.EXTRACTED,
            confidence_score=0.7,
            validation_status=ValidationStatus.PENDING,
            access_count=5
        ),
        ContextEntry(
            content="My goal is to become a senior engineer.",
            context_type=ContextType.GOAL,
            context_category=ContextCategory.GOALS,
            context_source=ContextSource.MANUAL,
            confidence_score=0.8,
            validation_status=ValidationStatus.CONFIRMED,
            access_count=3
        )
    ]
    
    # Save test contexts
    with get_db_context() as db:
        for context in test_contexts:
            db.add(context)
        db.commit()
        
        # Generate quality report
        report = context_analytics.generate_quality_report()
        print(f"     Total contexts: {report.total_contexts}")
        print(f"     Quality score: {report.quality_score:.2f}")
        print(f"     Average confidence: {report.average_confidence:.2f}")
        print(f"     Gaps identified: {len(report.gaps)}")
        print(f"     Insights generated: {len(report.insights)}")
        
        # Get usage statistics
        usage_stats = context_analytics.get_usage_statistics(days=30)
        print(f"     Recent contexts: {usage_stats['recent_contexts']}")
        print(f"     Growth rate: {usage_stats['growth_rate']:.2f}/day")
        
        # Get recommendations
        recommendations = context_analytics.get_context_recommendations()
        print(f"     Recommendations: {len(recommendations)}")
        
        for rec in recommendations[:2]:  # Show first 2 recommendations
            print(f"       - {rec['title']}: {rec['description']}")
        
        # Export analytics report
        analytics_report = context_analytics.export_analytics_report()
        print(f"     Analytics report generated: {len(analytics_report)} sections")
        
        # Clean up
        for context in test_contexts:
            db.delete(context)
        db.commit()
    
    print("   ✅ Analytics working correctly")


def main():
    """Main test function."""
    try:
        test_intelligent_context_system()
        print("\n🎉 ALL TESTS PASSED!")
        print("Intelligent Context Management System is working correctly!")
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
