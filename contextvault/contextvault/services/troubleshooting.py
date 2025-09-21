"""
Intelligent Troubleshooting System for ContextVault

This module provides comprehensive diagnostics, automatic issue detection,
and self-healing capabilities to ensure ContextVault always works.
"""

import logging
import requests
import subprocess
import time
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class TroubleshootingAgent:
    """Intelligent troubleshooting agent for ContextVault."""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        self.diagnostics_cache = {}
        
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        logger.info("Starting full ContextVault diagnostics...")
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "unknown",
            "issues": [],
            "fixes_applied": [],
            "components": {}
        }
        
        # Run component diagnostics
        diagnostics["components"] = {
            "dependencies": self._check_dependencies(),
            "database": self._check_database(),
            "ollama": self._check_ollama(),
            "proxy": self._check_proxy(),
            "context_retrieval": self._check_context_retrieval(),
            "permissions": self._check_permissions(),
            "semantic_search": self._check_semantic_search(),
        }
        
        # Determine overall health
        healthy_components = sum(1 for comp in diagnostics["components"].values() 
                               if comp.get("status") == "healthy")
        total_components = len(diagnostics["components"])
        
        if healthy_components == total_components:
            diagnostics["overall_health"] = "healthy"
        elif healthy_components >= total_components * 0.8:
            diagnostics["overall_health"] = "degraded"
        else:
            diagnostics["overall_health"] = "unhealthy"
        
        # Apply automatic fixes
        if diagnostics["overall_health"] != "healthy":
            diagnostics["fixes_applied"] = self._apply_automatic_fixes(diagnostics)
        
        diagnostics["issues"] = self.issues_found
        self.diagnostics_cache = diagnostics
        
        logger.info(f"Diagnostics complete: {diagnostics['overall_health']}")
        return diagnostics
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        # Check required dependencies
        required_deps = {
            "sqlalchemy": "Database ORM",
            "fastapi": "Web framework",
            "uvicorn": "ASGI server",
            "requests": "HTTP client",
            "pydantic": "Data validation"
        }
        
        for dep, description in required_deps.items():
            try:
                __import__(dep)
                result["details"][dep] = "available"
            except ImportError:
                result["details"][dep] = "missing"
                result["issues"].append(f"Missing required dependency: {dep} ({description})")
                result["status"] = "unhealthy"
        
        # Check optional dependencies
        optional_deps = {
            "sentence_transformers": "Semantic search (optional)",
            "sklearn": "Fallback semantic search (required if sentence_transformers missing)"
        }
        
        for dep, description in optional_deps.items():
            try:
                __import__(dep)
                result["details"][dep] = "available"
            except ImportError:
                result["details"][dep] = "missing"
                if dep == "sklearn":
                    result["issues"].append(f"Missing fallback dependency: {dep}")
                    result["status"] = "unhealthy"
                else:
                    result["details"][dep] = "optional_missing"
        
        return result
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and schema."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            from contextvault.database import get_db_context, engine
            from contextvault.models.context import ContextEntry
            
            # Test connection
            with get_db_context() as db:
                # Test basic query
                db.query(ContextEntry).limit(1).all()
                result["details"]["connection"] = "working"
                
                # Test table existence
                inspector = engine.inspect()
                tables = inspector.get_table_names()
                
                required_tables = ["context_entries", "permissions", "sessions"]
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    result["issues"].append(f"Missing database tables: {missing_tables}")
                    result["status"] = "unhealthy"
                else:
                    result["details"]["tables"] = "complete"
                
        except Exception as e:
            result["issues"].append(f"Database connection failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Check Ollama connectivity."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                
                result["details"]["connection"] = "working"
                result["details"]["models_count"] = len(models)
                
                if not models:
                    result["issues"].append("No Ollama models available")
                    result["status"] = "degraded"
                else:
                    result["details"]["models"] = [model.get("name", "unknown") for model in models]
                    
            else:
                result["issues"].append(f"Ollama API error: {response.status_code}")
                result["status"] = "unhealthy"
                
        except requests.exceptions.ConnectionError:
            result["issues"].append("Cannot connect to Ollama - is it running?")
            result["status"] = "unhealthy"
        except Exception as e:
            result["issues"].append(f"Ollama check failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _check_proxy(self) -> Dict[str, Any]:
        """Check ContextVault proxy status."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            response = requests.get("http://localhost:11435/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                # Check individual components
                proxy_healthy = health_data.get("proxy", {}).get("healthy", False)
                ollama_healthy = health_data.get("ollama", {}).get("status") == "healthy"
                db_healthy = health_data.get("database", {}).get("healthy", False)
                
                result["details"]["proxy"] = "running" if proxy_healthy else "unhealthy"
                result["details"]["ollama_integration"] = "working" if ollama_healthy else "failed"
                result["details"]["database_integration"] = "working" if db_healthy else "failed"
                
                if not all([proxy_healthy, ollama_healthy, db_healthy]):
                    result["issues"].append("Proxy components not all healthy")
                    result["status"] = "degraded"
                    
            else:
                result["issues"].append(f"Proxy health check failed: {response.status_code}")
                result["status"] = "unhealthy"
                
        except requests.exceptions.ConnectionError:
            result["issues"].append("ContextVault proxy not running")
            result["status"] = "unhealthy"
        except Exception as e:
            result["issues"].append(f"Proxy check failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _check_context_retrieval(self) -> Dict[str, Any]:
        """Check context retrieval functionality."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            from contextvault.database import get_db_context
            from contextvault.services.context_retrieval import ContextRetrievalService
            
            with get_db_context() as db:
                retrieval_service = ContextRetrievalService(db_session=db)
                
                # Test basic retrieval
                entries, metadata = retrieval_service.get_relevant_context(
                    model_id='test-model',
                    query_context='test query',
                    limit=5
                )
                
                result["details"]["basic_retrieval"] = "working"
                result["details"]["entries_found"] = len(entries)
                
                # Test with actual context
                from contextvault.models.context import ContextEntry
                context_count = db.query(ContextEntry).count()
                result["details"]["total_context_entries"] = context_count
                
                if context_count == 0:
                    result["issues"].append("No context entries found in database")
                    result["status"] = "degraded"
                
        except Exception as e:
            result["issues"].append(f"Context retrieval check failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check permission system."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            from contextvault.database import get_db_context
            from contextvault.models.permissions import Permission
            
            with get_db_context() as db:
                permissions = db.query(Permission).all()
                result["details"]["permission_count"] = len(permissions)
                
                # Check for default permissions
                mistral_permission = db.query(Permission).filter(
                    Permission.model_id == 'mistral:latest'
                ).first()
                
                if mistral_permission:
                    result["details"]["mistral_permissions"] = "configured"
                    result["details"]["allowed_scopes"] = mistral_permission.get_allowed_scopes()
                else:
                    result["issues"].append("No permissions configured for mistral:latest")
                    result["status"] = "degraded"
                
        except Exception as e:
            result["issues"].append(f"Permission check failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _check_semantic_search(self) -> Dict[str, Any]:
        """Check semantic search functionality."""
        result = {
            "status": "healthy",
            "details": {},
            "issues": []
        }
        
        try:
            from contextvault.services.semantic_search import get_semantic_search_service
            
            semantic_service = get_semantic_search_service()
            result["details"]["available"] = semantic_service.is_available()
            
            if semantic_service.is_available():
                cache_stats = semantic_service.get_cache_stats()
                result["details"]["cache_stats"] = cache_stats
                
                if cache_stats.get("fallback_mode"):
                    result["details"]["mode"] = "TF-IDF fallback"
                    result["status"] = "degraded"
                    result["issues"].append("Using TF-IDF fallback instead of sentence transformers")
                else:
                    result["details"]["mode"] = "sentence transformers"
            else:
                result["issues"].append("Semantic search not available")
                result["status"] = "unhealthy"
                
        except Exception as e:
            result["issues"].append(f"Semantic search check failed: {e}")
            result["status"] = "unhealthy"
        
        return result
    
    def _apply_automatic_fixes(self, diagnostics: Dict[str, Any]) -> List[str]:
        """Apply automatic fixes for common issues."""
        fixes_applied = []
        
        # Fix 1: Start Ollama if not running
        if diagnostics["components"]["ollama"]["status"] == "unhealthy":
            if self._try_start_ollama():
                fixes_applied.append("Started Ollama service")
        
        # Fix 2: Initialize database if missing tables
        if diagnostics["components"]["database"]["status"] == "unhealthy":
            if self._try_initialize_database():
                fixes_applied.append("Initialized database schema")
        
        # Fix 3: Start proxy if not running
        if diagnostics["components"]["proxy"]["status"] == "unhealthy":
            if self._try_start_proxy():
                fixes_applied.append("Started ContextVault proxy")
        
        # Fix 4: Create default permissions
        if diagnostics["components"]["permissions"]["status"] == "degraded":
            if self._try_create_default_permissions():
                fixes_applied.append("Created default permissions")
        
        # Fix 5: Add sample context if none exists
        if (diagnostics["components"]["context_retrieval"]["status"] == "degraded" and
            diagnostics["components"]["context_retrieval"]["details"].get("total_context_entries", 0) == 0):
            if self._try_add_sample_context():
                fixes_applied.append("Added sample context entries")
        
        return fixes_applied
    
    def _try_start_ollama(self) -> bool:
        """Try to start Ollama service."""
        try:
            # Check if Ollama is already running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return True
            
            # Try to start Ollama
            logger.info("Attempting to start Ollama...")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for it to start
            for i in range(10):
                time.sleep(1)
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code == 200:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
            return False
    
    def _try_initialize_database(self) -> bool:
        """Try to initialize database schema."""
        try:
            from contextvault.database import init_database
            init_database()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _try_start_proxy(self) -> bool:
        """Try to start ContextVault proxy."""
        try:
            # Kill any existing proxy
            subprocess.run(["pkill", "-f", "ollama_proxy.py"], capture_output=True)
            time.sleep(1)
            
            # Start new proxy
            proxy_path = Path(__file__).parent.parent.parent / "scripts" / "ollama_proxy.py"
            env = {**os.environ, "PYTHONPATH": str(proxy_path.parent.parent)}
            
            subprocess.Popen(
                ["python", str(proxy_path)],
                cwd=proxy_path.parent,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for it to start
            for i in range(10):
                time.sleep(1)
                try:
                    response = requests.get("http://localhost:11435/health", timeout=2)
                    if response.status_code == 200:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start proxy: {e}")
            return False
    
    def _try_create_default_permissions(self) -> bool:
        """Try to create default permissions."""
        try:
            from contextvault.database import get_db_context
            from contextvault.models.permissions import Permission
            
            with get_db_context() as db:
                # Check if permissions already exist
                existing = db.query(Permission).filter(
                    Permission.model_id == 'mistral:latest'
                ).first()
                
                if not existing:
                    # Create default permission
                    permission = Permission(
                        model_id='mistral:latest',
                        model_name='Mistral (Latest)',
                        scope='personal,work,preferences,notes',
                        is_active=True
                    )
                    db.add(permission)
                    db.commit()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to create default permissions: {e}")
            return False
    
    def _try_add_sample_context(self) -> bool:
        """Try to add sample context entries."""
        try:
            from contextvault.database import get_db_context
            from contextvault.models.context import ContextEntry
            
            with get_db_context() as db:
                # Check if context already exists
                existing_count = db.query(ContextEntry).count()
                if existing_count > 0:
                    return False
                
                # Add sample context
                sample_entries = [
                    {
                        'content': 'I am a software engineer who loves Python and testing. I prefer detailed explanations.',
                        'context_type': 'preference',
                        'source': 'sample',
                        'tags': ['python', 'testing', 'software', 'engineering']
                    },
                    {
                        'content': 'I have two cats named Luna and Pixel. They are playful and love string toys.',
                        'context_type': 'note',
                        'source': 'sample',
                        'tags': ['pets', 'cats', 'luna', 'pixel']
                    }
                ]
                
                for entry_data in sample_entries:
                    entry = ContextEntry(**entry_data)
                    db.add(entry)
                
                db.commit()
                return True
            
        except Exception as e:
            logger.error(f"Failed to add sample context: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        if not self.diagnostics_cache:
            self.run_full_diagnostics()
        
        return {
            "overall_health": self.diagnostics_cache.get("overall_health", "unknown"),
            "last_check": self.diagnostics_cache.get("timestamp"),
            "issues": self.diagnostics_cache.get("issues", []),
            "fixes_applied": self.diagnostics_cache.get("fixes_applied", [])
        }
    
    def force_health_check(self) -> Dict[str, Any]:
        """Force a fresh health check."""
        self.diagnostics_cache = {}
        return self.run_full_diagnostics()


# Global troubleshooting agent instance
_troubleshooting_agent = None

def get_troubleshooting_agent() -> TroubleshootingAgent:
    """Get the global troubleshooting agent instance."""
    global _troubleshooting_agent
    if _troubleshooting_agent is None:
        _troubleshooting_agent = TroubleshootingAgent()
    return _troubleshooting_agent
