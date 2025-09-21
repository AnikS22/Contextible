"""Model management service for multi-model support."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..database import get_db_context
from ..models.models import AIModel, ModelProvider, ModelStatus
from ..integrations import (
    ollama_integration,
    lmstudio_integration,
    jan_ai_integration,
    localai_integration,
    gpt4all_integration
)

logger = logging.getLogger(__name__)


class ModelManager:
    """Service for managing multiple AI models and their capabilities."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.integrations = {
            ModelProvider.OLLAMA: ollama_integration,
            ModelProvider.LM_STUDIO: lmstudio_integration,
            ModelProvider.JAN_AI: jan_ai_integration,
            ModelProvider.LOCALAI: localai_integration,
            ModelProvider.GPT4ALL: gpt4all_integration,
        }
        self.logger = logging.getLogger(__name__)
    
    async def discover_models(self) -> List[Dict[str, Any]]:
        """
        Discover all available models across all providers.
        
        Returns:
            List of discovered models with their information
        """
        discovered_models = []
        
        for provider, integration in self.integrations.items():
            try:
                self.logger.info(f"Discovering models for {provider.value}")
                models = await integration.get_available_models()
                
                for model in models:
                    model_info = {
                        "name": model.get("id", "unknown"),
                        "display_name": model.get("name", model.get("id", "unknown")),
                        "provider": provider.value,
                        "model_id": model.get("id"),
                        "capabilities": self._infer_capabilities(model),
                        "endpoint": integration.endpoint,
                        "status": "available"
                    }
                    discovered_models.append(model_info)
                
                self.logger.info(f"Found {len(models)} models for {provider.value}")
                
            except Exception as e:
                self.logger.error(f"Failed to discover models for {provider.value}: {e}")
                continue
        
        return discovered_models
    
    async def register_model(self, 
                           name: str,
                           provider: ModelProvider,
                           model_id: str,
                           capabilities: Optional[Dict[str, Any]] = None,
                           endpoint: Optional[str] = None,
                           **kwargs) -> AIModel:
        """
        Register a new AI model.
        
        Args:
            name: Model name
            provider: Model provider
            model_id: Provider-specific model ID
            capabilities: Model capabilities
            endpoint: API endpoint
            **kwargs: Additional model parameters
            
        Returns:
            Registered AIModel instance
        """
        with get_db_context() as db:
            # Check if model already exists
            existing_model = db.query(AIModel).filter(
                and_(
                    AIModel.provider == provider,
                    AIModel.model_id == model_id
                )
            ).first()
            
            if existing_model:
                self.logger.info(f"Model {name} already registered")
                return existing_model
            
            # Create new model
            model = AIModel.create_model(
                name=name,
                provider=provider,
                model_id=model_id,
                capabilities=capabilities or {},
                endpoint=endpoint,
                **kwargs
            )
            
            db.add(model)
            db.commit()
            db.refresh(model)
            
            self.logger.info(f"Registered model: {name} ({provider.value})")
            return model
    
    async def get_available_models(self, 
                                 provider: Optional[ModelProvider] = None,
                                 active_only: bool = True) -> List[AIModel]:
        """
        Get list of available models.
        
        Args:
            provider: Filter by specific provider
            active_only: Only return active models
            
        Returns:
            List of available models
        """
        with get_db_context() as db:
            query = db.query(AIModel)
            
            if provider:
                query = query.filter(AIModel.provider == provider)
            
            if active_only:
                query = query.filter(
                    and_(
                        AIModel.is_active == True,
                        AIModel.status == ModelStatus.ACTIVE
                    )
                )
            
            return query.all()
    
    async def get_model_by_id(self, model_id: str) -> Optional[AIModel]:
        """Get a specific model by ID."""
        with get_db_context() as db:
            return db.query(AIModel).filter(AIModel.id == model_id).first()
    
    async def get_model_by_name(self, name: str, provider: Optional[ModelProvider] = None) -> Optional[AIModel]:
        """Get a model by name and optionally provider."""
        with get_db_context() as db:
            query = db.query(AIModel).filter(AIModel.name == name)
            
            if provider:
                query = query.filter(AIModel.provider == provider)
            
            return query.first()
    
    async def update_model_status(self, model_id: str, status: ModelStatus) -> bool:
        """Update model status."""
        with get_db_context() as db:
            model = db.query(AIModel).filter(AIModel.id == model_id).first()
            if not model:
                return False
            
            model.status = status
            model.updated_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Updated model {model.name} status to {status.value}")
            return True
    
    async def update_model_performance(self, 
                                     model_id: str,
                                     response_time_ms: int,
                                     success: bool,
                                     tokens_generated: int = 0) -> bool:
        """Update model performance metrics."""
        with get_db_context() as db:
            model = db.query(AIModel).filter(AIModel.id == model_id).first()
            if not model:
                return False
            
            model.update_performance_metrics(response_time_ms, success, tokens_generated)
            db.commit()
            
            return True
    
    async def get_healthy_models(self) -> List[AIModel]:
        """Get all healthy models."""
        with get_db_context() as db:
            models = db.query(AIModel).filter(
                and_(
                    AIModel.is_active == True,
                    AIModel.status == ModelStatus.ACTIVE
                )
            ).all()
            
            # Filter by health score
            healthy_models = [model for model in models if model.is_healthy()]
            return healthy_models
    
    async def get_best_model_for_task(self, 
                                     task_type: str,
                                     context_types: List[str],
                                     user_preferences: Optional[Dict[str, Any]] = None) -> Optional[AIModel]:
        """
        Get the best model for a specific task.
        
        Args:
            task_type: Type of task (coding, creative, analysis, etc.)
            context_types: Types of context being used
            user_preferences: User preferences for model selection
            
        Returns:
            Best model for the task
        """
        with get_db_context() as db:
            models = await self.get_healthy_models()
            
            if not models:
                return None
            
            # Score models based on capabilities and performance
            scored_models = []
            for model in models:
                score = self._calculate_model_score(model, task_type, context_types, user_preferences)
                scored_models.append((model, score))
            
            # Sort by score and return best
            scored_models.sort(key=lambda x: x[1], reverse=True)
            return scored_models[0][0] if scored_models else None
    
    async def route_request(self, 
                           request_data: Dict[str, Any],
                           preferred_model: Optional[str] = None,
                           task_type: Optional[str] = None) -> Tuple[AIModel, Dict[str, Any]]:
        """
        Route a request to the best available model.
        
        Args:
            request_data: Request data
            preferred_model: Preferred model name
            task_type: Type of task
            
        Returns:
            Tuple of (selected_model, modified_request_data)
        """
        # Try preferred model first
        if preferred_model:
            model = await self.get_model_by_name(preferred_model)
            if model and model.is_healthy():
                integration = self.integrations.get(model.provider)
                if integration:
                    modified_request = await integration.inject_context(
                        request_data, model.model_id
                    )
                    return model, modified_request
        
        # Find best model for task
        if task_type:
            model = await self.get_best_model_for_task(task_type, [])
            if model:
                integration = self.integrations.get(model.provider)
                if integration:
                    modified_request = await integration.inject_context(
                        request_data, model.model_id
                    )
                    return model, modified_request
        
        # Fallback to any healthy model
        healthy_models = await self.get_healthy_models()
        if healthy_models:
            model = healthy_models[0]  # Take first available
            integration = self.integrations.get(model.provider)
            if integration:
                modified_request = await integration.inject_context(
                    request_data, model.model_id
                )
                return model, modified_request
        
        raise RuntimeError("No healthy models available")
    
    def _infer_capabilities(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Infer model capabilities from model information."""
        capabilities = {
            "coding": 0.5,
            "creative": 0.5,
            "analysis": 0.5,
            "reasoning": 0.5,
            "conversation": 0.5
        }
        
        model_name = model_info.get("id", "").lower()
        
        # Infer capabilities based on model name
        if "code" in model_name or "coder" in model_name:
            capabilities["coding"] = 0.9
        elif "creative" in model_name or "art" in model_name:
            capabilities["creative"] = 0.9
        elif "analysis" in model_name or "analytical" in model_name:
            capabilities["analysis"] = 0.9
        elif "reasoning" in model_name or "logic" in model_name:
            capabilities["reasoning"] = 0.9
        
        # Check model size for capability inference
        if "7b" in model_name or "13b" in model_name:
            # Larger models generally have better capabilities
            for key in capabilities:
                capabilities[key] = min(1.0, capabilities[key] + 0.2)
        
        return capabilities
    
    def _calculate_model_score(self, 
                             model: AIModel,
                             task_type: str,
                             context_types: List[str],
                             user_preferences: Optional[Dict[str, Any]] = None) -> float:
        """Calculate a score for model selection."""
        score = 0.0
        
        # Base capability score
        if model.capabilities and task_type in model.capabilities:
            score += model.capabilities[task_type].get("score", 0.0) * 0.4
        
        # Performance score
        if model.success_rate is not None:
            score += model.success_rate * 0.3
        
        # Response time score (faster is better)
        if model.average_response_time_ms is not None:
            if model.average_response_time_ms < 1000:
                score += 0.2
            elif model.average_response_time_ms < 3000:
                score += 0.1
        
        # Health score
        score += model.get_health_score() * 0.1
        
        return score
    
    async def sync_models(self) -> Dict[str, int]:
        """
        Sync models with all providers.
        
        Returns:
            Dictionary with sync results
        """
        results = {"discovered": 0, "registered": 0, "updated": 0}
        
        # Discover models from all providers
        discovered_models = await self.discover_models()
        results["discovered"] = len(discovered_models)
        
        # Register new models
        for model_info in discovered_models:
            try:
                provider = ModelProvider(model_info["provider"])
                model = await self.register_model(
                    name=model_info["name"],
                    provider=provider,
                    model_id=model_info["model_id"],
                    capabilities=model_info["capabilities"],
                    endpoint=model_info["endpoint"],
                    display_name=model_info["display_name"]
                )
                results["registered"] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to register model {model_info['name']}: {e}")
                continue
        
        return results


# Global model manager instance
model_manager = ModelManager()
