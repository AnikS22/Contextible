#!/usr/bin/env python3
"""Ollama proxy server with context injection."""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to Python path so we can import contextvault
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.config import settings, validate_environment
from contextvault.database import check_database_connection, init_database
from contextvault.integrations import ollama_integration


def setup_logging():
    """Setup logging for the proxy server."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


# Create lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the proxy server."""
    logger.info("Starting ContextVault Ollama Proxy")
    
    # Validate environment
    env_status = validate_environment()
    if env_status["status"] == "error":
        logger.error(f"Environment validation failed: {env_status['issues']}")
        raise RuntimeError(f"Environment issues: {', '.join(env_status['issues'])}")
    
    if env_status["warnings"]:
        logger.warning(f"Environment warnings: {env_status['warnings']}")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database")
        raise RuntimeError("Database connection failed")
    
    logger.info("ContextVault Ollama Proxy started successfully")
    yield
    logger.info("ContextVault Ollama Proxy shutting down")

# Create FastAPI app for the proxy
app = FastAPI(
    title="ContextVault Ollama Proxy",
    description="Proxy server that injects context into Ollama requests",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)




@app.get("/")
async def root():
    """Root endpoint with proxy information."""
    return {
        "name": "ContextVault Ollama Proxy",
        "version": "0.1.0",
        "description": "Proxy server that injects context into Ollama requests",
        "upstream": ollama_integration.endpoint,
        "proxy_port": settings.proxy_port,
        "ollama_port": settings.ollama_port,
        "context_injection": "enabled",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Ollama connectivity
    ollama_health = await ollama_integration.health_check()
    
    # Check database
    db_healthy = check_database_connection()
    
    status = "healthy"
    if not ollama_health["available"] or not db_healthy:
        status = "unhealthy"
    
    return {
        "status": status,
        "proxy": {
            "healthy": True,
            "endpoint": f"http://{settings.api_host}:{settings.proxy_port}",
        },
        "ollama": ollama_health,
        "database": {
            "healthy": db_healthy,
        },
        "context_injection": "enabled",
    }


@app.get("/api/tags")
async def get_models():
    """Proxy Ollama model list endpoint."""
    try:
        models = await ollama_integration.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@app.post("/api/pull")
async def pull_model(request: Request):
    """Proxy Ollama model pull endpoint."""
    try:
        body = await request.body()
        import json
        data = json.loads(body) if body else {}
        
        model_name = data.get("name")
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name is required")
        
        result = await ollama_integration.pull_model(model_name)
        
        if result["success"]:
            return {"status": "success", "message": result["message"]}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Failed to pull model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")


@app.post("/api/generate")
async def generate_with_context(request: Request):
    """Proxy Ollama generate endpoint with context injection."""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Use the integration's proxy method
        result = await ollama_integration.proxy_request(
            path="/api/generate",
            method="POST",
            headers=headers,
            body=body,
            inject_context=True,
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers=dict(result["headers"]),
        )
        
    except Exception as e:
        logger.error(f"Generate request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generate request failed: {str(e)}")


@app.post("/api/chat")
async def chat_with_context(request: Request):
    """Proxy Ollama chat endpoint with context injection."""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Use the integration's proxy method
        result = await ollama_integration.proxy_request(
            path="/api/chat",
            method="POST",
            headers=headers,
            body=body,
            inject_context=True,
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers=dict(result["headers"]),
        )
        
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_all_other_requests(request: Request, path: str):
    """Proxy all other Ollama API requests without context injection."""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Proxy without context injection for other endpoints
        result = await ollama_integration.proxy_request(
            path=f"/api/{path}",
            method=request.method,
            headers=headers,
            body=body,
            inject_context=False,
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers=dict(result["headers"]),
        )
        
    except Exception as e:
        logger.error(f"Proxy request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy request failed: {str(e)}")


@app.get("/context/status")
async def context_status():
    """Get context injection status and statistics."""
    try:
        from contextvault.services import vault_service
        
        stats = vault_service.get_context_stats()
        
        return {
            "context_injection": "enabled",
            "vault_stats": stats,
            "proxy_info": {
                "proxy_port": settings.proxy_port,
                "ollama_port": settings.ollama_port,
                "upstream": ollama_integration.endpoint,
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get context status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context status: {str(e)}")


@app.post("/context/toggle")
async def toggle_context_injection():
    """Toggle context injection on/off (placeholder for future feature)."""
    # This could be implemented to temporarily disable context injection
    return {
        "message": "Context injection toggle not implemented yet",
        "current_status": "enabled"
    }


def main():
    """Main function to run the proxy server."""
    setup_logging()
    
    print("🔗 Starting ContextVault Ollama Proxy")
    print(f"   Proxy Port: {settings.proxy_port}")
    print(f"   Ollama Port: {settings.ollama_port}")
    print(f"   Upstream: http://{settings.ollama_host}:{settings.ollama_port}")
    print()
    print("📡 Proxy endpoints:")
    print(f"   - Generate: http://localhost:{settings.proxy_port}/api/generate")
    print(f"   - Chat: http://localhost:{settings.proxy_port}/api/chat") 
    print(f"   - Models: http://localhost:{settings.proxy_port}/api/tags")
    print(f"   - Status: http://localhost:{settings.proxy_port}/context/status")
    print(f"   - Health: http://localhost:{settings.proxy_port}/health")
    print(f"   - Docs: http://localhost:{settings.proxy_port}/docs")
    print()
    print("💡 Usage:")
    print(f"   Instead of: curl http://localhost:{settings.ollama_port}/api/generate ...")
    print(f"   Use:        curl http://localhost:{settings.proxy_port}/api/generate ...")
    print()
    
    # Run the server
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.proxy_port,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
