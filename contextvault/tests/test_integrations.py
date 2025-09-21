"""Tests for ContextVault integrations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contextvault.database import Base
from contextvault.integrations import ollama_integration, OllamaIntegration
from contextvault.models import ContextEntry, ContextType, Session as SessionModel
from contextvault.services import vault_service


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integrations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestOllamaIntegration:
    """Test Ollama integration functionality."""
    
    def test_extract_model_id(self):
        """Test extracting model ID from request data."""
        integration = OllamaIntegration()
        
        # Test with model field
        request_data = {"model": "llama2", "prompt": "Hello"}
        model_id = integration.extract_model_id(request_data)
        assert model_id == "llama2"
        
        # Test without model field
        request_data = {"prompt": "Hello"}
        model_id = integration.extract_model_id(request_data)
        assert model_id is None
    
    def test_extract_prompt_generate(self):
        """Test extracting prompt from generate request."""
        integration = OllamaIntegration()
        
        # Test /api/generate format
        request_data = {
            "model": "llama2",
            "prompt": "What is Python?"
        }
        
        prompt = integration._extract_prompt(request_data)
        assert prompt == "What is Python?"
    
    def test_extract_prompt_chat(self):
        """Test extracting prompt from chat request."""
        integration = OllamaIntegration()
        
        # Test /api/chat format
        request_data = {
            "model": "llama2",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "What is Python?"}
            ]
        }
        
        prompt = integration._extract_prompt(request_data)
        assert prompt == "What is Python?"
    
    def test_extract_prompt_empty_messages(self):
        """Test extracting prompt with empty messages."""
        integration = OllamaIntegration()
        
        request_data = {
            "model": "llama2",
            "messages": []
        }
        
        prompt = integration._extract_prompt(request_data)
        assert prompt is None
    
    def test_format_prompt(self):
        """Test formatting prompt with context."""
        integration = OllamaIntegration()
        
        original_prompt = "What are my preferences?"
        context_entries = [
            "Preference: I like dark mode",
            "Preference: I prefer Python over JavaScript"
        ]
        
        formatted = integration.format_prompt(original_prompt, context_entries)
        
        assert "dark mode" in formatted
        assert "Python over JavaScript" in formatted
        assert "What are my preferences?" in formatted
    
    def test_inject_into_request_generate(self):
        """Test injecting context into generate request."""
        integration = OllamaIntegration()
        
        request_data = {
            "model": "llama2",
            "prompt": "Original prompt"
        }
        
        formatted_context = "Context: I like Python\n\nCurrent Conversation:\nOriginal prompt"
        
        modified_request = integration._inject_into_request(request_data, formatted_context)
        
        assert modified_request["model"] == "llama2"
        assert modified_request["prompt"] == formatted_context
    
    def test_inject_into_request_chat(self):
        """Test injecting context into chat request."""
        integration = OllamaIntegration()
        
        request_data = {
            "model": "llama2",
            "messages": [
                {"role": "user", "content": "Original prompt"}
            ]
        }
        
        formatted_context = "Context: I like Python\n\nCurrent Conversation:\nOriginal prompt"
        
        modified_request = integration._inject_into_request(request_data, formatted_context)
        
        assert modified_request["model"] == "llama2"
        assert len(modified_request["messages"]) == 1
        assert modified_request["messages"][0]["content"] == formatted_context
    
    @pytest.mark.asyncio
    async def test_inject_context(self, setup_database):
        """Test full context injection process."""
        integration = OllamaIntegration()
        
        # Create some test context
        vault_service.save_context(
            content="I prefer dark mode interfaces",
            context_type=ContextType.PREFERENCE,
            tags=["ui", "preferences"]
        )
        
        # Create a test session
        session = SessionModel.create_session("llama2", source="test")
        
        # Test request
        request_data = {
            "model": "llama2",
            "prompt": "What are my UI preferences?"
        }
        
        # Mock the context retrieval to avoid dependency issues
        with patch('contextvault.integrations.ollama.context_retrieval_service') as mock_service:
            mock_service.get_context_for_prompt.return_value = {
                "formatted_context": "Previous Context:\nI prefer dark mode interfaces\n\nCurrent Conversation:\nWhat are my UI preferences?",
                "context_entries": [
                    {
                        "id": "test-id",
                        "content": "I prefer dark mode interfaces",
                        "context_type": "preference"
                    }
                ],
                "total_length": 100
            }
            
            # Inject context
            modified_request = await integration.inject_context(
                request_data, "llama2", session
            )
            
            # Verify context was injected
            assert "dark mode" in modified_request["prompt"]
            assert "UI preferences" in modified_request["prompt"]
    
    @pytest.mark.asyncio
    async def test_inject_context_no_relevant_context(self, setup_database):
        """Test context injection when no relevant context is found."""
        integration = OllamaIntegration()
        
        request_data = {
            "model": "llama2",
            "prompt": "What is quantum physics?"
        }
        
        # Mock empty context response
        with patch('contextvault.integrations.ollama.context_retrieval_service') as mock_service:
            mock_service.get_context_for_prompt.return_value = {
                "context_entries": [],
                "total_length": 0
            }
            
            # Inject context
            modified_request = await integration.inject_context(
                request_data, "llama2", None
            )
            
            # Should return original request unchanged
            assert modified_request == request_data
    
    @pytest.mark.asyncio
    async def test_inject_context_error_handling(self, setup_database):
        """Test context injection error handling."""
        integration = OllamaIntegration()
        
        request_data = {
            "model": "llama2",
            "prompt": "Test prompt"
        }
        
        # Mock an error in context retrieval
        with patch('contextvault.integrations.ollama.context_retrieval_service') as mock_service:
            mock_service.get_context_for_prompt.side_effect = Exception("Context service error")
            
            # Inject context - should handle error gracefully
            modified_request = await integration.inject_context(
                request_data, "llama2", None
            )
            
            # Should return original request on error
            assert modified_request == request_data
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with successful connection."""
        integration = OllamaIntegration()
        
        # Mock successful HTTP response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            health = await integration.health_check()
            
            assert health["integration"] == "ollama"
            assert health["status"] == "healthy"
            assert health["available"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with connection failure."""
        integration = OllamaIntegration()
        
        # Mock connection error
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            
            health = await integration.health_check()
            
            assert health["integration"] == "ollama"
            assert health["status"] == "unhealthy"
            assert health["available"] is False
            assert "error" in health
    
    @pytest.mark.asyncio
    async def test_check_model_availability(self):
        """Test checking if a model is available."""
        integration = OllamaIntegration()
        
        # Mock successful response with model list
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2"},
                    {"name": "codellama"},
                    {"name": "mistral"}
                ]
            }
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            # Test existing model
            available = await integration.check_model_availability("llama2")
            assert available is True
            
            # Test non-existing model
            available = await integration.check_model_availability("nonexistent")
            assert available is False
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models."""
        integration = OllamaIntegration()
        
        # Mock successful response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {
                        "name": "llama2",
                        "size": 3800000000,
                        "modified_at": "2023-01-01T00:00:00Z",
                        "digest": "abc123"
                    }
                ]
            }
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            models = await integration.get_available_models()
            
            assert len(models) == 1
            assert models[0]["id"] == "llama2"
            assert models[0]["name"] == "llama2"
            assert models[0]["size"] == 3800000000
    
    @pytest.mark.asyncio
    async def test_generate_response(self, setup_database):
        """Test generating response with context injection."""
        integration = OllamaIntegration()
        
        # Mock successful generation
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Python is a programming language...",
                "model": "llama2",
                "done": True
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Mock context injection
            with patch.object(integration, 'inject_context') as mock_inject:
                mock_inject.return_value = {
                    "model": "llama2",
                    "prompt": "Context-injected prompt"
                }
                
                result = await integration.generate_response(
                    model_id="llama2",
                    prompt="What is Python?",
                    inject_context=True
                )
                
                assert result["success"] is True
                assert result["response"] == "Python is a programming language..."
                assert result["context_injected"] is True
    
    @pytest.mark.asyncio
    async def test_chat(self, setup_database):
        """Test chat with context injection."""
        integration = OllamaIntegration()
        
        # Mock successful chat
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"role": "assistant", "content": "Hello! How can I help you?"},
                "model": "llama2",
                "done": True
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Mock context injection
            with patch.object(integration, 'inject_context') as mock_inject:
                mock_inject.return_value = {
                    "model": "llama2",
                    "messages": [{"role": "user", "content": "Context-injected message"}]
                }
                
                result = await integration.chat(
                    model_id="llama2",
                    messages=[{"role": "user", "content": "Hello"}],
                    inject_context=True
                )
                
                assert result["success"] is True
                assert result["message"]["content"] == "Hello! How can I help you?"
                assert result["context_injected"] is True
    
    def test_create_session(self):
        """Test creating a session for tracking."""
        integration = OllamaIntegration()
        
        session = integration.create_session(
            model_id="llama2",
            source="test",
            user_id="test-user"
        )
        
        assert session.model_id == "llama2"
        assert session.source == "test"
        assert session.user_id == "test-user"
        assert session.session_type == "chat"
    
    def test_get_integration_info(self):
        """Test getting integration information."""
        integration = OllamaIntegration()
        
        info = integration.get_integration_info()
        
        assert info["name"] == "ollama"
        assert info["type"] == "ai_model_integration"
        assert "endpoint" in info
        assert "capabilities" in info
        assert info["capabilities"]["context_injection"] is True


class TestBaseIntegration:
    """Test base integration functionality."""
    
    def test_log_request(self):
        """Test request logging."""
        from contextvault.integrations.base import BaseIntegration
        
        integration = BaseIntegration("test", "localhost", 8000)
        
        # Test successful request logging
        integration.log_request(
            model_id="test_model",
            request_type="generate",
            success=True,
            context_count=5,
            processing_time_ms=150
        )
        
        # Test failed request logging
        integration.log_request(
            model_id="test_model",
            request_type="chat",
            success=False,
            error="Connection timeout"
        )
        
        # Should not raise any exceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
