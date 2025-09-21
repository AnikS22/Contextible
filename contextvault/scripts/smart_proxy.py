#!/usr/bin/env python3
"""
Smart Proxy that automatically redirects Ollama traffic to ContextVault
"""

import asyncio
import json
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Contextible Smart Proxy")

# ContextVault endpoint
CONTEXTVULT_ENDPOINT = "http://localhost:11435"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_all_requests(path: str, request: Request):
    """Proxy all requests to ContextVault with automatic context injection."""
    
    # Get request body
    body = await request.body()
    
    # Forward to ContextVault
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{CONTEXTVULT_ENDPOINT}/{path}",
                headers=dict(request.headers),
                content=body,
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return Response(
                content=f"Error: {str(e)}",
                status_code=500,
                media_type="text/plain"
            )

if __name__ == "__main__":
    print("🚀 Starting Contextible Smart Proxy...")
    print("   This proxy automatically adds context to all Ollama requests!")
    print("   Just use Ollama normally - no settings needed!")
    uvicorn.run(app, host="127.0.0.1", port=11434)
