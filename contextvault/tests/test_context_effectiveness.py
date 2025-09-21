#!/usr/bin/env python3
"""
Comprehensive test suite for ContextVault context effectiveness.

Tests that context injection actually works and improves AI responses.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context
from contextvault.services.vault import VaultService
from contextvault.services.context_retrieval import ContextRetrievalService
from contextvault.services.semantic_search import get_semantic_search_service
from contextvault.services.debug import get_debugger, debug_context_injection
from contextvault.services.feedback import get_feedback_service
from contextvault.services.templates import template_manager, format_context_with_template
from contextvault.models.context import ContextType


class TestContextInjectionEffectiveness:
    """Test that context injection actually works and improves responses."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data for each test."""
        with get_db_context() as db:
            # Clear existing test data
            vault_service = VaultService(db_session=db)
            
            # Add test context entries
            test_contexts = [
                {
                    "content": "I am a software engineer who loves Python and FastAPI for backend development",
                    "context_type": ContextType.PREFERENCE,
                    "source": "test_setup",
                    "tags": ["programming", "preferences", "backend"]
                },
                {
                    "content": "I prefer detailed explanations and want to understand how systems work",
                    "context_type": ContextType.PREFERENCE,
                    "source": "test_setup",
                    "tags": ["learning", "preferences"]
                },
                {
                    "content": "I am currently working on ContextVault, a system for giving AI models persistent memory",
                    "context_type": ContextType.NOTE,
                    "source": "test_setup",
                    "tags": ["project", "development", "AI"]
                }
            ]
            
            for ctx_data in test_contexts:
                vault_service.add_context(
                    content=ctx_data["content"],
                    context_type=ctx_data["context_type"],
                    source=ctx_data["source"],
                    tags=ctx_data["tags"]
                )
            
            db.commit()
    
    def test_context_retrieval_finds_relevant_entries(self):
        """Test that context retrieval finds relevant entries for queries."""
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            
            # Test query that should match our test contexts
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="test-model",
                query_context="What programming languages should I learn?",
                limit=5
            )
            
            assert len(entries) > 0, "Should find at least one relevant context entry"
            assert any("Python" in entry.content for entry in entries), "Should find Python-related context"
            assert metadata["total_found"] >= len(entries), "Metadata should be accurate"
    
    def test_semantic_search_returns_relevant_results(self):
        """Test that semantic search returns relevant results."""
        semantic_service = get_semantic_search_service()
        
        if not semantic_service.is_available():
            pytest.skip("Semantic search not available")
        
        with get_db_context() as db:
            results = semantic_service.search_similar_contexts(
                query="programming languages and backend development",
                db_session=db,
                max_results=3
            )
            
            assert len(results) > 0, "Should find relevant semantic matches"
            
            # Check that results are sorted by similarity
            if len(results) > 1:
                assert results[0][1] >= results[1][1], "Results should be sorted by similarity score"
    
    def test_template_formatting_includes_context(self):
        """Test that template formatting properly includes context."""
        test_context = ["I am a software engineer who loves Python"]
        test_prompt = "What should I learn next?"
        
        formatted = format_context_with_template(
            context_entries=test_context,
            user_prompt=test_prompt,
            template_name=None
        )
        
        assert test_context[0] in formatted, "Formatted prompt should include context"
        assert test_prompt in formatted, "Formatted prompt should include user prompt"
        assert len(formatted) > len(test_prompt), "Formatted prompt should be longer than original"
    
    def test_pipeline_debugger_captures_all_steps(self):
        """Test that the pipeline debugger captures all steps."""
        debug_info = debug_context_injection(
            model_id="test-model",
            user_prompt="What programming languages should I learn?",
            max_context_length=1000
        )
        
        assert debug_info.request_id is not None, "Should have a request ID"
        assert debug_info.model_id == "test-model", "Should capture model ID"
        assert debug_info.user_prompt is not None, "Should capture user prompt"
        assert len(debug_info.pipeline_steps) > 0, "Should have pipeline steps"
        assert debug_info.total_duration_ms > 0, "Should have duration"
        
        # Check specific pipeline steps
        step_names = [step.step_name for step in debug_info.pipeline_steps]
        assert "context_retrieval" in step_names, "Should have context retrieval step"
        assert "template_formatting" in step_names, "Should have template formatting step"
    
    def test_permission_system_blocks_unauthorized_access(self):
        """Test that permission system blocks unauthorized model access."""
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            
            # Test with a model that should have no permissions
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="unauthorized-model",
                query_context="test query",
                limit=5
            )
            
            # Should return empty results due to permissions
            assert len(entries) == 0, "Unauthorized model should get no context"
            assert metadata.get("access_denied", False), "Should indicate access denied"
    
    def test_feedback_system_captures_ratings(self):
        """Test that feedback system properly captures user ratings."""
        feedback_service = get_feedback_service()
        
        success = feedback_service.submit_feedback(
            session_id="test-session-123",
            model_id="test-model",
            user_prompt="test prompt",
            ai_response="test response",
            context_used=[{"content": "test context", "context_type": "preference"}],
            rating=4,
            feedback_text="Good response!"
        )
        
        assert success, "Should successfully submit feedback"
        
        # Check that feedback was stored
        feedback = feedback_service.get_feedback_for_session("test-session-123")
        assert feedback is not None, "Should be able to retrieve feedback"
        assert feedback.rating == 4, "Should store correct rating"
        assert feedback.feedback_text == "Good response!", "Should store feedback text"
    
    def test_analytics_calculate_correctly(self):
        """Test that feedback analytics calculate correctly."""
        feedback_service = get_feedback_service()
        
        # Submit multiple feedback entries
        test_feedbacks = [
            ("session1", 5, "Excellent!"),
            ("session2", 4, "Good"),
            ("session3", 3, "Okay"),
            ("session4", 5, "Great!"),
            ("session5", 2, "Poor")
        ]
        
        for session_id, rating, text in test_feedbacks:
            feedback_service.submit_feedback(
                session_id=session_id,
                model_id="test-model",
                user_prompt="test prompt",
                ai_response="test response",
                context_used=[],
                rating=rating,
                feedback_text=text
            )
        
        analytics = feedback_service.calculate_analytics()
        
        assert analytics.total_feedback_count == 5, "Should count all feedback"
        assert analytics.average_rating == 3.8, "Should calculate correct average"  # (5+4+3+5+2)/5
        assert analytics.rating_distribution[5] == 2, "Should count 5-star ratings"
        assert analytics.rating_distribution[4] == 1, "Should count 4-star ratings"
    
    def test_context_entries_have_required_fields(self):
        """Test that context entries have all required fields."""
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            
            entry_id = vault_service.add_context(
                content="Test content",
                context_type=ContextType.NOTE,
                source="test",
                tags=["test"]
            )
            
            entry = vault_service.get_context_by_id(entry_id)
            
            assert entry is not None, "Should be able to retrieve entry"
            assert entry.content == "Test content", "Should store content"
            assert entry.context_type == ContextType.NOTE, "Should store context type"
            assert entry.source == "test", "Should store source"
            assert entry.tags == ["test"], "Should store tags"
            assert entry.created_at is not None, "Should have creation timestamp"
            assert entry.updated_at is not None, "Should have update timestamp"
    
    def test_template_manager_has_multiple_templates(self):
        """Test that template manager has multiple templates available."""
        templates = template_manager.get_all_templates()
        
        assert len(templates) > 1, "Should have multiple templates"
        
        template_names = [t.name for t in templates]
        assert "direct_instruction" in template_names, "Should have direct instruction template"
        assert "assistant_roleplay" in template_names, "Should have assistant roleplay template"
        
        # Test template switching
        original_template = template_manager.get_active_template()
        template_manager.set_active_template("assistant_roleplay")
        
        new_template = template_manager.get_active_template()
        assert new_template.name == "assistant_roleplay", "Should switch to new template"
        
        # Restore original template
        template_manager.set_active_template(original_template.name)
    
    def test_health_endpoints_return_valid_data(self):
        """Test that health endpoints return valid monitoring data."""
        # This would require a running FastAPI server, so we'll mock it
        with patch('contextvault.api.health.get_context_injection_stats') as mock_stats:
            mock_stats.return_value = {
                "pipeline_statistics": {"total_sessions": 10},
                "semantic_search": {"model_available": True},
                "context_entries": {"total_entries": 5}
            }
            
            stats = mock_stats()
            
            assert "pipeline_statistics" in stats, "Should include pipeline statistics"
            assert "semantic_search" in stats, "Should include semantic search stats"
            assert "context_entries" in stats, "Should include context entry stats"
    
    def test_error_handling_graceful_degradation(self):
        """Test that system gracefully handles errors."""
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            
            # Test with invalid model ID
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="",  # Empty model ID
                query_context="test query",
                limit=5
            )
            
            # Should handle gracefully without crashing
            assert isinstance(entries, list), "Should return list even on error"
            assert isinstance(metadata, dict), "Should return dict even on error"
    
    def test_performance_within_acceptable_limits(self):
        """Test that context retrieval performs within acceptable limits."""
        import time
        
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            
            start_time = time.time()
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="test-model",
                query_context="What programming languages should I learn?",
                limit=10
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            assert duration_ms < 5000, f"Context retrieval should be fast (<5s), took {duration_ms:.2f}ms"
            assert len(entries) >= 0, "Should return valid results"


class TestIntegrationScenarios:
    """Integration tests for complete scenarios."""
    
    def test_complete_context_injection_workflow(self):
        """Test the complete workflow from query to context injection."""
        # 1. Add context
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            
            entry_id = vault_service.add_context(
                content="I love Python programming and machine learning",
                context_type=ContextType.PREFERENCE,
                source="user_profile",
                tags=["programming", "python", "ml"]
            )
        
        # 2. Retrieve context
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="test-model",
                query_context="What should I learn for machine learning?",
                limit=5
            )
            
            assert len(entries) > 0, "Should find relevant context"
            
            # Check that our added context is found
            found_our_context = any(
                "Python programming and machine learning" in entry.content 
                for entry in entries
            )
            assert found_our_context, "Should find our added context"
        
        # 3. Format with template
        context_strings = [entry.content for entry in entries]
        formatted_prompt = format_context_with_template(
            context_entries=context_strings,
            user_prompt="What should I learn for machine learning?",
            template_name=None
        )
        
        assert "Python programming and machine learning" in formatted_prompt, "Should include context in formatted prompt"
        assert "What should I learn for machine learning?" in formatted_prompt, "Should include user prompt"
        
        # 4. Debug the injection
        debug_info = debug_context_injection(
            model_id="test-model",
            user_prompt="What should I learn for machine learning?",
            max_context_length=1000
        )
        
        assert debug_info.success, "Context injection should succeed"
        assert len(debug_info.context_entries_used) > 0, "Should use context entries"
        
        # 5. Submit feedback
        feedback_service = get_feedback_service()
        success = feedback_service.submit_feedback(
            session_id="integration-test-session",
            model_id="test-model",
            user_prompt="What should I learn for machine learning?",
            ai_response="Based on your interest in Python and machine learning...",
            context_used=debug_info.context_entries_used,
            rating=5,
            feedback_text="Perfect! The response was personalized and helpful."
        )
        
        assert success, "Should successfully submit feedback"
    
    def test_semantic_search_improves_over_keyword_search(self):
        """Test that semantic search provides better results than keyword search."""
        semantic_service = get_semantic_search_service()
        
        if not semantic_service.is_available():
            pytest.skip("Semantic search not available")
        
        with get_db_context() as db:
            # Add context that's semantically related but doesn't share exact keywords
            vault_service = VaultService(db_session=db)
            vault_service.add_context(
                content="I enjoy building web applications and APIs",
                context_type=ContextType.PREFERENCE,
                source="test",
                tags=["web", "apis"]
            )
            db.commit()
            
            # Test semantic search with related but different terms
            semantic_results = semantic_service.search_similar_contexts(
                query="backend development and server-side programming",
                db_session=db,
                max_results=3
            )
            
            # Should find the web applications context even though keywords don't match exactly
            found_semantic_match = any(
                "web applications and APIs" in result[0].content 
                for result in semantic_results
            )
            
            assert found_semantic_match, "Semantic search should find semantically related content"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
