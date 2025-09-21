"""
Real Data Fetching for ContextVault CLI
Get actual system data instead of mock data
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextvault.database import get_db_context
from contextvault.models.context import ContextEntry, ContextCategory, ContextSource, ValidationStatus


class RealDataFetcher:
    """Fetch real data from ContextVault system."""
    
    @staticmethod
    def get_context_stats() -> Dict[str, Any]:
        """Get real context statistics."""
        try:
            with get_db_context() as db:
                total_contexts = db.query(ContextEntry).count()
                
                # Get counts by source
                manual_count = db.query(ContextEntry).filter(
                    ContextEntry.context_source == ContextSource.MANUAL
                ).count()
                
                extracted_count = db.query(ContextEntry).filter(
                    ContextEntry.context_source == ContextSource.EXTRACTED
                ).count()
                
                conversation_count = db.query(ContextEntry).filter(
                    ContextEntry.context_source == ContextSource.CONVERSATION
                ).count()
                
                # Get counts by category
                category_counts = {}
                for category in ContextCategory:
                    count = db.query(ContextEntry).filter(
                        ContextEntry.context_category == category
                    ).count()
                    if count > 0:
                        category_counts[category.value] = count
                
                # Get recent contexts (last 7 days)
                from datetime import datetime, timedelta
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_count = db.query(ContextEntry).filter(
                    ContextEntry.created_at >= week_ago
                ).count()
                
                return {
                    "total_contexts": total_contexts,
                    "manual_contexts": manual_count,
                    "extracted_contexts": extracted_count,
                    "conversation_contexts": conversation_count,
                    "recent_contexts": recent_count,
                    "category_counts": category_counts,
                    "status": "connected"
                }
        except Exception as e:
            return {
                "total_contexts": 0,
                "manual_contexts": 0,
                "extracted_contexts": 0,
                "conversation_contexts": 0,
                "recent_contexts": 0,
                "category_counts": {},
                "status": f"error: {str(e)}"
            }
    
    @staticmethod
    def get_recent_contexts(limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent context entries."""
        try:
            with get_db_context() as db:
                contexts = db.query(ContextEntry).order_by(
                    ContextEntry.created_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        "content": ctx.content[:100] + "..." if len(ctx.content) > 100 else ctx.content,
                        "category": ctx.context_category.value if ctx.context_category else "unknown",
                        "source": ctx.context_source.value if ctx.context_source else "unknown",
                        "confidence": ctx.confidence_score,
                        "created_at": ctx.created_at.strftime("%Y-%m-%d %H:%M") if ctx.created_at else "unknown",
                        "validation_status": ctx.validation_status.value if ctx.validation_status else "unknown"
                    }
                    for ctx in contexts
                ]
        except Exception as e:
            return [{"error": str(e)}]
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get real system health status."""
        health_status = {
            "database": "unknown",
            "api_server": "unknown", 
            "ollama_proxy": "unknown",
            "ollama_core": "unknown"
        }
        
        # Test database
        try:
            with get_db_context() as db:
                db.query(ContextEntry).count()
                health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
        
        # Test API server
        try:
            import requests
            response = requests.get("http://localhost:8000/health/", timeout=2)
            if response.status_code == 200:
                health_status["api_server"] = "healthy"
            else:
                health_status["api_server"] = f"unhealthy: {response.status_code}"
        except Exception as e:
            health_status["api_server"] = f"error: {str(e)}"
        
        # Test Ollama proxy
        try:
            import requests
            response = requests.get("http://localhost:11435/health", timeout=2)
            if response.status_code == 200:
                health_status["ollama_proxy"] = "healthy"
            else:
                health_status["ollama_proxy"] = f"unhealthy: {response.status_code}"
        except Exception as e:
            health_status["ollama_proxy"] = f"error: {str(e)}"
        
        # Test Ollama core
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                health_status["ollama_core"] = f"healthy ({len(models)} models)"
            else:
                health_status["ollama_core"] = f"unhealthy: {response.status_code}"
        except Exception as e:
            health_status["ollama_core"] = f"error: {str(e)}"
        
        return health_status
    
    @staticmethod
    def get_actual_context_injection_status() -> Dict[str, Any]:
        """Check if context injection is actually working."""
        try:
            import requests
            import json
            
            # Test if we can make a request through the proxy
            test_prompt = "What do you know about me?"
            response = requests.post(
                "http://localhost:11435/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": test_prompt,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                
                # Check if the response seems personalized (not generic)
                personalized_indicators = [
                    "you mentioned", "you told me", "you said", "your context",
                    "based on your", "from your", "you have", "you are"
                ]
                
                is_personalized = any(indicator in ai_response.lower() for indicator in personalized_indicators)
                
                return {
                    "injection_working": True,
                    "response_received": True,
                    "is_personalized": is_personalized,
                    "response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                    "status": "working" if is_personalized else "working but not personalized"
                }
            else:
                return {
                    "injection_working": False,
                    "response_received": False,
                    "status": f"proxy error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "injection_working": False,
                "response_received": False,
                "status": f"error: {str(e)}"
            }
