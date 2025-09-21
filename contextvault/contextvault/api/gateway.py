"""API Gateway for Contextible enterprise features."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..models.users import User, UserRole
from ..services.user_context import user_context_service
from ..services.model_manager import model_manager
from ..services.analytics_enhanced import enhanced_analytics
from ..services.import_export import import_export_service

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# API Router
router = APIRouter(prefix="/api/v1", tags=["enterprise"])


# Pydantic Models
class ChatRequest(BaseModel):
    """Chat request model."""
    prompt: str = Field(..., description="User prompt")
    model_id: Optional[str] = Field(None, description="Preferred model ID")
    max_context_length: int = Field(4000, description="Maximum context length")
    include_context: bool = Field(True, description="Whether to include context")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Model response")
    model_used: str = Field(..., description="Model that was used")
    context_used: List[Dict[str, Any]] = Field(default_factory=list, description="Context entries used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    session_id: str = Field(..., description="Session ID")


class ContextCreateRequest(BaseModel):
    """Context creation request model."""
    content: str = Field(..., description="Context content")
    context_type: str = Field("text", description="Type of context")
    context_category: str = Field("other", description="Category of context")
    tags: List[str] = Field(default_factory=list, description="Tags for context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ContextResponse(BaseModel):
    """Context response model."""
    id: str = Field(..., description="Context ID")
    content: str = Field(..., description="Context content")
    context_type: str = Field(..., description="Type of context")
    context_category: str = Field(..., description="Category of context")
    tags: List[str] = Field(default_factory=list, description="Tags")
    created_at: str = Field(..., description="Creation timestamp")
    user_id: str = Field(..., description="User ID")


class UserStatsResponse(BaseModel):
    """User statistics response model."""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")
    total_context_entries: int = Field(..., description="Total context entries")
    total_sessions: int = Field(..., description="Total sessions")
    last_activity_at: Optional[str] = Field(None, description="Last activity timestamp")


# Authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """Get current authenticated user."""
    # In a real implementation, you would validate the token/credentials
    # For now, we'll use a simple API key lookup
    api_key = credentials.credentials
    
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user or not user.is_active_user():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user"
        )
    
    return user


# Rate Limiting (simplified)
class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self):
        self.requests = {}
    
    async def check_rate_limit(self, user_id: str, limit: int = 100) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.utcnow()
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        key = f"{user_id}:{minute_key}"
        
        if key not in self.requests:
            self.requests[key] = 0
        
        self.requests[key] += 1
        
        # Clean old entries
        cutoff = now - timedelta(minutes=5)
        keys_to_remove = [k for k in self.requests.keys() if k.split(":")[1] < cutoff.strftime("%Y-%m-%d-%H-%M")]
        for k in keys_to_remove:
            del self.requests[k]
        
        return self.requests[key] <= limit


rate_limiter = RateLimiter()


# API Endpoints

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Chat endpoint with context injection."""
    try:
        # Check rate limit
        if not await rate_limiter.check_rate_limit(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Get user context
        context_entries = await user_context_service.get_user_context(
            user_id=current_user.id,
            model_id=request.model_id or "default",
            request={"prompt": request.prompt},
            max_context_length=request.max_context_length
        )
        
        # Route to appropriate model
        model, modified_request = await model_manager.route_request(
            request_data={"prompt": request.prompt, "model": request.model_id},
            preferred_model=request.model_id,
            task_type="chat"
        )
        
        # Create session
        session = await user_context_service.create_user_session(
            user_id=current_user.id,
            model_id=model.model_id,
            session_type="chat",
            source="api"
        )
        
        # Process request (simplified - in real implementation, you'd call the model)
        response_text = f"Response to: {request.prompt}"
        
        # Update session
        if session:
            session.complete_session(success=True, response_summary=response_text[:100])
            db.commit()
        
        # Update analytics
        await enhanced_analytics.track_model_performance(
            model_id=model.model_id,
            metrics={
                "response_time_ms": 1000,  # Placeholder
                "success": True,
                "tokens_generated": len(response_text)
            }
        )
        
        return ChatResponse(
            response=response_text,
            model_used=model.name,
            context_used=[{"id": ctx.id, "content": ctx.content[:100]} for ctx in context_entries],
            processing_time_ms=1000,
            session_id=session.id if session else "unknown"
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/context", response_model=ContextResponse)
async def create_context_endpoint(
    request: ContextCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a new context entry."""
    try:
        # Check rate limit
        if not await rate_limiter.check_rate_limit(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Create context entry
        context_entry = await user_context_service.create_user_context(
            user_id=current_user.id,
            content=request.content,
            context_type=request.context_type,
            context_category=request.context_category,
            source="api",
            tags=request.tags,
            metadata=request.metadata
        )
        
        if not context_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create context entry"
            )
        
        return ContextResponse(
            id=context_entry.id,
            content=context_entry.content,
            context_type=context_entry.context_type.value if hasattr(context_entry.context_type, 'value') else str(context_entry.context_type),
            context_category=context_entry.context_category.value if hasattr(context_entry.context_category, 'value') else str(context_entry.context_category),
            tags=context_entry.tags or [],
            created_at=context_entry.created_at.isoformat(),
            user_id=context_entry.user_id
        )
        
    except Exception as e:
        logger.error(f"Create context endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/context", response_model=List[ContextResponse])
async def get_context_endpoint(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get user's context entries."""
    try:
        # Get user context
        context_entries = await user_context_service.get_user_context(
            user_id=current_user.id,
            model_id="default",
            request={},
            max_context_length=10000
        )
        
        # Apply pagination
        paginated_entries = context_entries[offset:offset + limit]
        
        return [
            ContextResponse(
                id=entry.id,
                content=entry.content,
                context_type=entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type),
                context_category=entry.context_category.value if hasattr(entry.context_category, 'value') else str(entry.context_category),
                tags=entry.tags or [],
                created_at=entry.created_at.isoformat(),
                user_id=entry.user_id
            )
            for entry in paginated_entries
        ]
        
    except Exception as e:
        logger.error(f"Get context endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_models_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Get available models."""
    try:
        models = await model_manager.get_available_models()
        return [model.to_dict() for model in models]
        
    except Exception as e:
        logger.error(f"Get models endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Get user statistics."""
    try:
        stats = await user_context_service.get_user_statistics(current_user.id)
        return UserStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Get user stats endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Get analytics data."""
    try:
        if not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        analytics = await enhanced_analytics.get_usage_patterns(days=30)
        return analytics
        
    except Exception as e:
        logger.error(f"Get analytics endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/export")
async def export_data_endpoint(
    format: str = "json",
    current_user: User = Depends(get_current_user)
):
    """Export user data."""
    try:
        export_data = await import_export_service.export_context(
            format=format,
            user_id=current_user.id,
            include_sessions=True
        )
        
        return {"data": export_data, "format": format}
        
    except Exception as e:
        logger.error(f"Export data endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check_endpoint():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
