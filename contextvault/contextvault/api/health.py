"""Health check endpoints for ContextVault."""

import time
import psutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db_session, get_database_info, check_database_connection
from ..models import ContextEntry, Permission, Session as SessionModel
from ..schemas.responses import HealthResponse
from ..config import settings
from ..services.debug import get_debugger
from ..services.semantic_search import get_semantic_search_service

router = APIRouter()


def get_context_injection_stats(db: Session) -> Dict[str, Any]:
    """Get context injection statistics."""
    try:
        # Get debugger statistics
        debugger = get_debugger()
        debug_stats = debugger.get_pipeline_statistics()
        
        # Get semantic search statistics
        semantic_service = get_semantic_search_service()
        semantic_stats = semantic_service.get_cache_stats()
        
        # Get context entry statistics
        total_entries = db.query(ContextEntry).count()
        entries_with_embeddings = db.query(ContextEntry).filter(ContextEntry.embedding.isnot(None)).count()
        
        # Get most accessed context entries
        most_accessed = db.query(ContextEntry).order_by(ContextEntry.access_count.desc()).limit(5).all()
        most_accessed_data = [
            {
                "id": entry.id,
                "content_preview": entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                "context_type": entry.context_type.value,
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed_at.isoformat() if entry.last_accessed_at else None
            }
            for entry in most_accessed
        ]
        
        # Get recent context entries
        recent_entries = db.query(ContextEntry).order_by(ContextEntry.created_at.desc()).limit(5).all()
        recent_entries_data = [
            {
                "id": entry.id,
                "content_preview": entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                "context_type": entry.context_type.value,
                "created_at": entry.created_at.isoformat(),
                "source": entry.source
            }
            for entry in recent_entries
        ]
        
        return {
            "pipeline_statistics": debug_stats,
            "semantic_search": semantic_stats,
            "context_entries": {
                "total_entries": total_entries,
                "entries_with_embeddings": entries_with_embeddings,
                "embedding_coverage": entries_with_embeddings / total_entries if total_entries > 0 else 0
            },
            "most_accessed_entries": most_accessed_data,
            "recent_entries": recent_entries_data,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        }


def get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_usage_mb = (memory.total - memory.available) / 1024 / 1024
        
        # Get CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        return {
            "memory_usage_mb": round(memory_usage_mb, 2),
            "cpu_usage_percent": round(cpu_usage, 2),
            "disk_usage_percent": round(disk_usage_percent, 2),
        }
    except Exception:
        return {
            "memory_usage_mb": None,
            "cpu_usage_percent": None,
            "disk_usage_percent": None,
        }


def get_database_metrics(db: Session) -> Dict[str, Any]:
    """Get database-related metrics."""
    try:
        # Count entities
        context_count = db.query(ContextEntry).count()
        permission_count = db.query(Permission).count()
        session_count = db.query(SessionModel).count()
        
        return {
            "total_context_entries": context_count,
            "total_permissions": permission_count,
            "total_sessions": session_count,
        }
    except Exception:
        return {
            "total_context_entries": 0,
            "total_permissions": 0,
            "total_sessions": 0,
        }


def check_integrations() -> Dict[str, Any]:
    """Check status of external integrations."""
    integrations = {}
    
    # Check Ollama connectivity
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((settings.ollama_host, settings.ollama_port))
        sock.close()
        
        integrations["ollama"] = {
            "status": "healthy" if result == 0 else "unreachable",
            "endpoint": f"http://{settings.ollama_host}:{settings.ollama_port}",
            "last_checked": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        integrations["ollama"] = {
            "status": "error",
            "error": str(e),
            "endpoint": f"http://{settings.ollama_host}:{settings.ollama_port}",
            "last_checked": datetime.utcnow().isoformat(),
        }
    
    return integrations


@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db_session)):
    """
    Comprehensive health check endpoint.
    
    Returns detailed health information including:
    - Overall application status
    - Database connectivity
    - System metrics
    - Integration status
    - Application metrics
    """
    warnings = []
    issues = []
    
    # Check database
    db_healthy = check_database_connection()
    database_info = get_database_info()
    
    if not db_healthy:
        issues.append("Database connection failed")
        overall_status = "unhealthy"
    else:
        overall_status = "healthy"
    
    # Get system metrics
    system_metrics = get_system_metrics()
    
    # Check for performance warnings
    if system_metrics.get("memory_usage_mb", 0) > 1000:  # > 1GB
        warnings.append("High memory usage detected")
    
    if system_metrics.get("cpu_usage_percent", 0) > 80:
        warnings.append("High CPU usage detected")
    
    if system_metrics.get("disk_usage_percent", 0) > 90:
        warnings.append("High disk usage detected")
    
    # Get database metrics
    db_metrics = get_database_metrics(db) if db_healthy else {
        "total_context_entries": 0,
        "total_permissions": 0,
        "total_sessions": 0,
    }
    
    # Check integrations
    integrations = check_integrations()
    
    # Check for integration warnings
    for name, info in integrations.items():
        if info["status"] != "healthy":
            warnings.append(f"{name.title()} integration is {info['status']}")
    
    # Determine final status
    if issues:
        final_status = "unhealthy"
    elif warnings:
        final_status = "degraded" 
    else:
        final_status = "healthy"
    
    # Calculate uptime (simplified - would need proper startup tracking in production)
    uptime_seconds = 0.0
    try:
        from ..main import app
        startup_time = getattr(app.state, 'startup_time', time.time())
        uptime_seconds = time.time() - startup_time
    except:
        uptime_seconds = 0.0
    
    return HealthResponse(
        status=final_status,
        version="0.1.0",
        uptime_seconds=uptime_seconds,
        database=database_info,
        integrations=integrations,
        warnings=warnings,
        issues=issues,
        **system_metrics,
        **db_metrics,
    )


@router.get("/live", include_in_schema=False)
async def liveness_probe():
    """
    Simple liveness probe for orchestration platforms.
    
    Returns 200 OK if the application is running.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db_session)):
    """
    Readiness probe for orchestration platforms.
    
    Returns 200 OK if the application is ready to serve requests.
    Checks database connectivity and other critical dependencies.
    """
    # Check database
    if not check_database_connection():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Perform a simple database query
    try:
        db.query(ContextEntry).count()
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database query failed")
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
    }


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db_session)):
    """
    Get application metrics in a format suitable for monitoring.
    
    Returns metrics about:
    - Database entities
    - System performance
    - Integration status
    """
    # Database metrics
    db_metrics = get_database_metrics(db)
    
    # System metrics
    system_metrics = get_system_metrics()
    
    # Integration metrics
    integrations = check_integrations()
    integration_metrics = {}
    for name, info in integrations.items():
        integration_metrics[f"{name}_status"] = 1 if info["status"] == "healthy" else 0
    
    # Combine all metrics
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_metrics,
        "system": system_metrics,
        "integrations": integration_metrics,
        "application": {
            "version": "0.1.0",
            "environment": getattr(settings, 'environment', 'production'),
        }
    }
    
    return metrics


@router.get("/context-stats")
async def get_context_injection_statistics(db: Session = Depends(get_db_session)):
    """
    Get detailed context injection statistics and monitoring data.
    
    Returns comprehensive information about:
    - Context injection pipeline performance
    - Semantic search effectiveness
    - Most/least used context entries
    - Recent context injection examples
    """
    return get_context_injection_stats(db)


@router.get("/context-examples")
async def get_recent_context_examples(db: Session = Depends(get_db_session), limit: int = 5):
    """
    Get recent context injection examples for debugging and analysis.
    
    Returns recent debug sessions showing:
    - What context was retrieved for specific queries
    - How context was formatted and injected
    - Performance metrics for each injection
    """
    try:
        debugger = get_debugger()
        recent_sessions = debugger.get_recent_debug_sessions(limit)
        
        examples = []
        for session in recent_sessions:
            example = {
                "request_id": session.request_id,
                "model_id": session.model_id,
                "user_prompt": session.user_prompt,
                "timestamp": session.timestamp.isoformat(),
                "success": session.success,
                "total_duration_ms": session.total_duration_ms,
                "context_entries_count": len(session.context_entries_used),
                "context_entries": [
                    {
                        "content_preview": entry["content"][:100] + "..." if len(entry["content"]) > 100 else entry["content"],
                        "context_type": entry["context_type"],
                        "relevance_score": entry.get("relevance_score", 0.0),
                        "tags": entry.get("tags", [])
                    }
                    for entry in session.context_entries_used[:3]  # Show first 3 entries
                ],
                "final_prompt_preview": session.final_prompt[:200] + "..." if len(session.final_prompt) > 200 else session.final_prompt,
                "error_message": session.error_message
            }
            examples.append(example)
        
        return {
            "examples": examples,
            "total_available": len(debugger.debug_sessions),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        }
