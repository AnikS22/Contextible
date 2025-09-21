#!/usr/bin/env python3
"""
Auto-proxy that intercepts Ollama traffic on port 11434
Users don't need to change any settings - just run this script
"""

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
from contextvault.integrations.ollama import OllamaIntegration

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging for the auto-proxy server."""
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
    """Initialize the auto-proxy server."""
    logger.info("🚀 Starting ContextVault Auto-Proxy")
    logger.info("   This intercepts Ollama traffic on port 11434")
    logger.info("   Users don't need to change any settings!")
    
    # Validate environment
    env_status = validate_environment()
    if env_status["status"] == "error":
        logger.error(f"Environment validation failed: {env_status['issues']}")
        raise RuntimeError(f"Environment issues: {', '.join(env_status['issues'])}")
    
    if env_status["warnings"]:
        logger.warning(f"Environment warnings: {env_status['warnings']}")
    
    # Initialize database
    try:
        await init_database()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed")
        raise RuntimeError("Database connection failed")
    
    # Initialize Ollama integration (connect to real Ollama on port 11435)
    global ollama_integration
    ollama_integration = OllamaIntegration(host="127.0.0.1", port=11435)
    
    # Check if real Ollama is running
    health = await ollama_integration.check_ollama_health()
    if not health.get("available"):
        logger.error("Real Ollama server not found on port 11435")
        logger.error("Please start Ollama on port 11435 or update the auto-proxy configuration")
        raise RuntimeError("Real Ollama server not available")
    
    logger.info("✅ ContextVault Auto-Proxy started successfully")
    logger.info("📡 Ollama traffic on port 11434 is now enhanced with persistent memory!")
    logger.info("🔗 Connected to real Ollama server on port 11435")
    
    yield
    
    logger.info("ContextVault Auto-Proxy shutting down")

# Create FastAPI app
app = FastAPI(
    title="ContextVault Auto-Proxy",
    description="Automatically enhances Ollama with persistent memory - no configuration needed!",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with information."""
    return {
        "message": "ContextVault Auto-Proxy",
        "description": "Your Ollama is now enhanced with persistent memory!",
        "status": "running",
        "features": [
            "Persistent memory across conversations",
            "Automatic context injection",
            "Conversation learning",
            "Cross-model memory sharing"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "proxy": {
            "healthy": True,
            "endpoint": "http://127.0.0.1:11434"
        },
        "ollama": await ollama_integration.check_ollama_health() if 'ollama_integration' in globals() else {"available": False},
        "database": {
            "healthy": check_database_connection()
        },
        "context_injection": "enabled"
    }

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

@app.get("/api/tags")
async def list_models():
    """Proxy Ollama models list endpoint."""
    try:
        result = await ollama_integration.proxy_request(
            path="/api/tags",
            method="GET",
            headers={},
            body=b"",
            inject_context=False,
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers=dict(result["headers"]),
        )
        
    except Exception as e:
        logger.error(f"Models list request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Models list request failed: {str(e)}")

@app.post("/api/pull")
async def pull_model(request: Request):
    """Proxy Ollama model pull endpoint."""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        result = await ollama_integration.proxy_request(
            path="/api/pull",
            method="POST",
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
        logger.error(f"Model pull request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model pull request failed: {str(e)}")

if __name__ == "__main__":
    setup_logging()
    
    print("🚀 ContextVault Auto-Proxy")
    print("=" * 40)
    print("This automatically enhances your Ollama with persistent memory!")
    print("No configuration needed - just run this script.")
    print("")
    print("📡 Your Ollama client will work exactly the same,")
    print("   but now with persistent memory across conversations.")
    print("")
    print("🎯 Features enabled:")
    print("   • Automatic context injection")
    print("   • Conversation learning") 
    print("   • Cross-model memory sharing")
    print("   • Persistent user preferences")
    print("")
    print("⚡ Starting server on port 11434...")
    print("   (This will intercept your Ollama traffic)")
    print("")
    
    # Run the server on port 11434 to intercept Ollama traffic
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=11434,  # This intercepts the default Ollama port!
        log_level="info"
    )
