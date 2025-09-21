"""
Comprehensive Health Check Service for ContextVault
"""

import time
import requests
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

from ..config import settings
from ..database import get_db_context
from ..integrations import ollama_integration


class HealthCheckService:
    """Service for checking ContextVault system health."""
    
    def __init__(self):
        self.timeout = 5.0
    
    async def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of all components."""
        start_time = time.time()
        
        checks = {
            "api_server": self.check_api_server(),
            "ollama_proxy": self.check_ollama_proxy(),
            "ollama_core": self.check_ollama_core(),
            "database": self.check_database(),
            "context_retrieval": self.check_context_retrieval(),
            "template_system": self.check_template_system(),
            "mcp_integration": self.check_mcp_integration(),
        }
        
        # Run checks concurrently
        results = {}
        for name, check_coro in checks.items():
            try:
                results[name] = await asyncio.wait_for(check_coro, timeout=self.timeout)
            except asyncio.TimeoutError:
                results[name] = {
                    "status": "timeout",
                    "message": f"Check timed out after {self.timeout}s",
                    "healthy": False
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "message": str(e),
                    "healthy": False
                }
        
        # Calculate overall health
        overall_healthy = all(result.get("healthy", False) for result in results.values())
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "overall_healthy": overall_healthy,
            "check_duration_ms": int((time.time() - start_time) * 1000),
            "timestamp": time.time(),
            "checks": results
        }
    
    async def check_api_server(self) -> Dict[str, Any]:
        """Check API server health."""
        try:
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{settings.api_port}/health/",
                timeout=self.timeout
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "message": f"API responding on port {settings.api_port}",
                    "healthy": True,
                    "response_time_ms": response_time,
                    "details": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"API returned status {response.status_code}",
                    "healthy": False,
                    "response_time_ms": response_time
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "message": "Cannot connect to API server",
                "healthy": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_ollama_proxy(self) -> Dict[str, Any]:
        """Check Ollama proxy health."""
        try:
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{settings.proxy_port}/health",
                timeout=self.timeout
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "message": f"Proxy responding on port {settings.proxy_port}",
                    "healthy": True,
                    "response_time_ms": response_time,
                    "details": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Proxy returned status {response.status_code}",
                    "healthy": False,
                    "response_time_ms": response_time
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "message": "Cannot connect to proxy server",
                "healthy": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_ollama_core(self) -> Dict[str, Any]:
        """Check Ollama core health."""
        try:
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{settings.ollama_port}/api/tags",
                timeout=self.timeout
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "healthy",
                    "message": f"Ollama responding with {len(models)} models",
                    "healthy": True,
                    "response_time_ms": response_time,
                    "details": {
                        "models": [m.get("name") for m in models],
                        "model_count": len(models)
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Ollama returned status {response.status_code}",
                    "healthy": False,
                    "response_time_ms": response_time
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "message": "Cannot connect to Ollama",
                "healthy": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            start_time = time.time()
            
            # Check database connection
            with get_db_context() as db:
                # Test query
                from ..models import ContextEntry
                total_entries = db.query(ContextEntry).count()
                
                # Check for recent entries
                recent_entries = db.query(ContextEntry).order_by(
                    ContextEntry.created_at.desc()
                ).limit(5).all()
                
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "message": f"Database connected with {total_entries} entries",
                "healthy": True,
                "response_time_ms": response_time,
                "details": {
                    "total_entries": total_entries,
                    "recent_entries": len(recent_entries)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_context_retrieval(self) -> Dict[str, Any]:
        """Check context retrieval system."""
        try:
            start_time = time.time()
            
            # Test context retrieval
            from ..services.context_retrieval import ContextRetrievalService
            
            with get_db_context() as db:
                retrieval_service = ContextRetrievalService(db_session=db)
                result = retrieval_service.get_context_for_prompt(
                    model_id="test_model",
                    user_prompt="test query",
                    max_context_length=1000
                )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if result.get("error"):
                return {
                    "status": "unhealthy",
                    "message": f"Context retrieval failed: {result['error']}",
                    "healthy": False,
                    "response_time_ms": response_time
                }
            else:
                entries_retrieved = len(result.get("context_entries", []))
                return {
                    "status": "healthy",
                    "message": f"Retrieved {entries_retrieved} context entries",
                    "healthy": True,
                    "response_time_ms": response_time,
                    "details": {
                        "entries_retrieved": entries_retrieved,
                        "total_length": result.get("total_length", 0)
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_template_system(self) -> Dict[str, Any]:
        """Check template system."""
        try:
            start_time = time.time()
            
            from ..services.templates import template_manager
            
            # Test template formatting
            templates = template_manager.get_all_templates()
            sample_context = ["Test context entry"]
            sample_prompt = "Test prompt"
            
            formatted = template_manager.format_context(
                context_entries=sample_context,
                user_prompt=sample_prompt
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "message": f"Template system working with {len(templates)} templates",
                "healthy": True,
                "response_time_ms": response_time,
                "details": {
                    "template_count": len(templates),
                    "active_template": template_manager.current_template,
                    "formatted_length": len(formatted)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    async def check_mcp_integration(self) -> Dict[str, Any]:
        """Check MCP integration."""
        try:
            start_time = time.time()
            
            # Check if MCP is enabled and working
            from ..integrations.mcp.manager import MCPManager
            
            mcp_manager = MCPManager()
            
            # Try to get connections (this will fail if no MCP servers configured)
            try:
                connections = await mcp_manager.get_connections()
                providers = await mcp_manager.get_providers()
                
                response_time = int((time.time() - start_time) * 1000)
                
                return {
                    "status": "partial",
                    "message": f"MCP integration available with {len(connections)} connections",
                    "healthy": True,
                    "response_time_ms": response_time,
                    "details": {
                        "connections": len(connections),
                        "providers": len(providers)
                    }
                }
                
            except Exception:
                return {
                    "status": "partial",
                    "message": "MCP integration available but no servers configured",
                    "healthy": True,
                    "response_time_ms": 0,
                    "details": {
                        "connections": 0,
                        "providers": 0,
                        "note": "Run 'contextvault mcp setup' to configure"
                    }
                }
                
        except ImportError:
            return {
                "status": "disabled",
                "message": "MCP integration not available",
                "healthy": True,
                "response_time_ms": 0,
                "details": {
                    "note": "MCP integration is optional"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "healthy": False
            }
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick status without async operations."""
        status = {
            "timestamp": time.time(),
            "services": {}
        }
        
        # Quick API check
        try:
            response = requests.get(
                f"http://localhost:{settings.api_port}/health/",
                timeout=2
            )
            status["services"]["api"] = {
                "running": response.status_code == 200,
                "port": settings.api_port
            }
        except:
            status["services"]["api"] = {
                "running": False,
                "port": settings.api_port
            }
        
        # Quick proxy check
        try:
            response = requests.get(
                f"http://localhost:{settings.proxy_port}/health",
                timeout=2
            )
            status["services"]["proxy"] = {
                "running": response.status_code == 200,
                "port": settings.proxy_port
            }
        except:
            status["services"]["proxy"] = {
                "running": False,
                "port": settings.proxy_port
            }
        
        # Quick Ollama check
        try:
            response = requests.get(
                f"http://localhost:{settings.ollama_port}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                status["services"]["ollama"] = {
                    "running": True,
                    "port": settings.ollama_port,
                    "models": len(models)
                }
            else:
                status["services"]["ollama"] = {
                    "running": False,
                    "port": settings.ollama_port
                }
        except:
            status["services"]["ollama"] = {
                "running": False,
                "port": settings.ollama_port
            }
        
        # Database check
        try:
            with get_db_context() as db:
                from ..models import ContextEntry
                total_entries = db.query(ContextEntry).count()
                status["database"] = {
                    "connected": True,
                    "entries": total_entries
                }
        except:
            status["database"] = {
                "connected": False,
                "entries": 0
            }
        
        return status


# Global health check service instance
health_service = HealthCheckService()
