"""Simple working vault service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..database import get_db_context
from ..models.context import ContextEntry, ContextType

logger = logging.getLogger(__name__)


class SimpleVaultService:
    """Simple working vault service."""
    
    def save_context(
        self,
        content: str,
        context_type: ContextType = ContextType.TEXT,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a context entry."""
        try:
            with get_db_context() as db:
                entry = ContextEntry(
                    content=content,
                    context_type=context_type,
                    source=source,
                    tags=tags,
                    user_id=user_id,
                )
                db.add(entry)
                db.commit()
                db.refresh(entry)
                
                return {
                    "id": entry.id,
                    "content": entry.content,
                    "context_type": str(entry.context_type),
                    "source": entry.source,
                    "tags": entry.tags,
                    "user_id": entry.user_id,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            raise RuntimeError(f"Failed to save context: {e}")
    
    def get_context(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get context entries."""
        try:
            with get_db_context() as db:
                entries = db.query(ContextEntry).offset(offset).limit(limit).all()
                total = db.query(ContextEntry).count()
                
                entries_dict = []
                for entry in entries:
                    entries_dict.append({
                        "id": entry.id,
                        "content": entry.content,
                        "context_type": str(entry.context_type),
                        "source": entry.source,
                        "tags": entry.tags,
                        "user_id": entry.user_id,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat()
                    })
                
                return entries_dict, total
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            raise RuntimeError(f"Failed to get context: {e}")
    
    def search_context(
        self,
        query: str,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search context entries."""
        try:
            with get_db_context() as db:
                entries = db.query(ContextEntry).filter(
                    ContextEntry.content.ilike(f"%{query}%")
                ).limit(limit).all()
                
                entries_dict = []
                for entry in entries:
                    entries_dict.append({
                        "id": entry.id,
                        "content": entry.content,
                        "context_type": str(entry.context_type),
                        "source": entry.source,
                        "tags": entry.tags,
                        "user_id": entry.user_id,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat()
                    })
                
                return entries_dict, len(entries_dict)
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            raise RuntimeError(f"Failed to search context: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        try:
            with get_db_context() as db:
                total_entries = db.query(ContextEntry).count()
                
                return {
                    "total_entries": total_entries,
                    "status": "healthy"
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise RuntimeError(f"Failed to get stats: {e}")


# Global simple vault service instance
simple_vault_service = SimpleVaultService()
