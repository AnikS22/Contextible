"""Main FastAPI application for ContextVault."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings, validate_environment
from .database import init_database, check_database_connection
from .api import context, permissions, health, mcp
from .schemas.responses import ErrorResponse
from .services.semantic_search import initialize_semantic_search

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True,
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting ContextVault application")
    
    try:
        # Validate environment
        env_status = validate_environment()
        if env_status["status"] == "error":
            logger.error("Environment validation failed", issues=env_status["issues"])
            raise RuntimeError(f"Environment issues: {', '.join(env_status['issues'])}")
        
        if env_status["warnings"]:
            logger.warning("Environment warnings", warnings=env_status["warnings"])
        
        # Initialize database
        if not check_database_connection():
            raise RuntimeError("Cannot connect to database")
        
        init_database()
        logger.info("Database initialized successfully")
        
        # Initialize semantic search
        semantic_search_available = initialize_semantic_search()
        if semantic_search_available:
            logger.info("Semantic search initialized successfully")
        else:
            logger.warning("Semantic search initialization failed - will use keyword search fallback")
        
        # Store startup time
        app.state.startup_time = time.time()
        
        logger.info("ContextVault application started successfully")
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ContextVault application")


# Create FastAPI application
app = FastAPI(
    title="ContextVault",
    description="Local-first context management layer for AI models",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    logger.warning(f"Value error: {str(exc)} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "details": {"type": "ValueError"}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)} - {request.method} {request.url}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An internal error occurred",
            "details": {"type": type(exc).__name__} if settings.log_level == "DEBUG" else None
        }
    )


# Include API routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    context.router,
    prefix="/api/context",
    tags=["Context Management"]
)

app.include_router(
    permissions.router,
    prefix="/api/permissions",
    tags=["Permission Management"]
)

app.include_router(
    mcp.router,
    prefix="/api",
    tags=["MCP Integration"]
)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "ContextVault",
        "version": "0.1.0",
        "description": "Local-first context management layer for AI models",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_version": "v1",
    }


# Application metadata endpoint
@app.get("/info", tags=["System"])
async def get_app_info():
    """Get application information and configuration."""
    uptime = time.time() - getattr(app.state, 'startup_time', time.time())
    
    return {
        "application": {
            "name": "ContextVault",
            "version": "0.1.0",
            "description": "Local-first context management layer for AI models",
            "uptime_seconds": round(uptime, 2),
        },
        "api": {
            "version": "v1",
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
        },
        "configuration": {
            "max_context_entries": settings.max_context_entries,
            "max_context_length": settings.max_context_length,
            "cache_enabled": settings.enable_caching,
            "ollama_integration": {
                "host": settings.ollama_host,
                "port": settings.ollama_port,
                "proxy_port": settings.proxy_port,
            }
        },
        "environment": validate_environment(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "contextvault.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        reload=settings.log_level == "DEBUG",
        access_log=True,
    )
