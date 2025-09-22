"""Core vault operations service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from ..database import get_db_context
from ..models import ContextEntry, ContextType
from ..config import settings

logger = logging.getLogger(__name__)


class VaultService:
    """Core service for context vault operations."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the vault service."""
        self.db_session = db_session
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db_context())
    
    def save_context(
        self,
        content: str,
        context_type: ContextType = ContextType.TEXT,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a new context entry to the vault.
        
        Args:
            content: The context content
            context_type: Type of context (text, file, event, preference, note)
            source: Source of the context
            tags: List of tags for categorization
            metadata: Additional metadata
            user_id: User ID (for multi-user support)
            session_id: Session ID where this context was created
            
        Returns:
            Dictionary with created context entry data
            
        Raises:
            ValueError: If content is empty or too long
            RuntimeError: If database operation fails
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        
        if len(content) > settings.max_context_length:
            raise ValueError(f"Content exceeds maximum length of {settings.max_context_length} characters")
        
        # Clean and validate tags
        clean_tags = []
        if tags:
            for tag in tags:
                if tag and isinstance(tag, str):
                    clean_tag = tag.strip().lower()
                    if clean_tag and clean_tag not in clean_tags:
                        clean_tags.append(clean_tag)
        
        try:
            # Use provided session or create a new one
            if self.db_session:
                # Use existing session (caller manages commits)
                db = self.db_session
                
                entry = ContextEntry(
                    content=content.strip(),
                    context_type=context_type,
                    source=source,
                    tags=clean_tags if clean_tags else None,
                    entry_metadata=metadata or {},
                    user_id=user_id,
                    session_id=session_id,
                )
                
                db.add(entry)
                db.flush()  # Ensure ID is generated
                db.refresh(entry)
                
                logger.info(
                    f"Context entry saved: {entry.id}, type={context_type}, length={len(content)}, tags={clean_tags}"
                )
                
                return {
                    "id": entry.id,
                    "content": entry.content,
                    "context_type": entry.context_type.value,
                    "source": entry.source,
                    "tags": entry.tags,
                    "user_id": entry.user_id,
                    "session_id": entry.session_id,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat()
                }
                
            else:
                # Create new session context (we manage commits)
                with get_db_context() as db:
                    entry = ContextEntry(
                        content=content.strip(),
                        context_type=context_type,
                        source=source,
                        tags=clean_tags if clean_tags else None,
                        entry_metadata=metadata or {},
                        user_id=user_id,
                        session_id=session_id,
                    )
                    
                    db.add(entry)
                    db.commit()
                    db.refresh(entry)
                    
                    logger.info(
                        f"Context entry saved: {entry.id}, type={context_type}, length={len(content)}, tags={clean_tags}"
                    )
                    
                    return {
                        "id": entry.id,
                        "content": entry.content,
                        "context_type": entry.context_type.value,
                        "source": entry.source,
                        "tags": entry.tags,
                        "user_id": entry.user_id,
                        "session_id": entry.session_id,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat()
                    }
                
        except Exception as e:
            logger.error(f"Failed to save context entry: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to save context entry: {str(e)}")
    
    def get_context(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve context entries with filtering.
        
        Args:
            filters: Dictionary of filters to apply
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            Tuple of (entries_as_dicts, total_count)
        """
        filters = filters or {}
        
        try:
            with get_db_context() as db:
                query = db.query(ContextEntry)
                
                # Apply filters
                conditions = []
                
                # Context type filter
                if "context_types" in filters and filters["context_types"]:
                    conditions.append(ContextEntry.context_type.in_(filters["context_types"]))
                
                # Tags filter
                if "tags" in filters and filters["tags"]:
                    tag_conditions = []
                    for tag in filters["tags"]:
                        tag_conditions.append(ContextEntry.tags.contains([tag]))
                    conditions.append(or_(*tag_conditions))
                
                # Source filter
                if "source" in filters and filters["source"]:
                    conditions.append(ContextEntry.source.ilike(f"%{filters['source']}%"))
                
                # Date range filter
                if "since" in filters and filters["since"]:
                    conditions.append(ContextEntry.created_at >= filters["since"])
                
                if "until" in filters and filters["until"]:
                    conditions.append(ContextEntry.created_at <= filters["until"])
                
                # User filter
                if "user_id" in filters and filters["user_id"]:
                    conditions.append(ContextEntry.user_id == filters["user_id"])
                
                # Session filter
                if "session_id" in filters and filters["session_id"]:
                    conditions.append(ContextEntry.session_id == filters["session_id"])
                
                # Text search
                if "search" in filters and filters["search"]:
                    search_term = filters["search"]
                    search_conditions = [
                        ContextEntry.content.ilike(f"%{search_term}%"),
                        ContextEntry.source.ilike(f"%{search_term}%"),
                    ]
                    conditions.append(or_(*search_conditions))
                
                # Apply all conditions
                if conditions:
                    query = query.filter(and_(*conditions))
                
                # Get total count before pagination
                total = query.count()
                
                # Apply ordering
                if hasattr(ContextEntry, order_by):
                    order_column = getattr(ContextEntry, order_by)
                    if order_desc:
                        query = query.order_by(desc(order_column))
                    else:
                        query = query.order_by(order_column)
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Execute query
                entries = query.all()
                
                # Convert to dictionaries
                entries_dict = []
                for entry in entries:
                    entries_dict.append({
                        "id": entry.id,
                        "content": entry.content,
                        "context_type": entry.context_type.value,
                        "source": entry.source,
                        "tags": entry.tags,
                        "user_id": entry.user_id,
                        "session_id": entry.session_id,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat(),
                        "access_count": entry.access_count
                    })
                
                return entries_dict, total
            
        except Exception as e:
            logger.error("Failed to retrieve context", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to retrieve context: {str(e)}")
    
    def update_context(
        self,
        entry_id: str,
        updates: Dict[str, Any],
    ) -> Optional[ContextEntry]:
        """
        Update a context entry.
        
        Args:
            entry_id: ID of the entry to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated ContextEntry or None if not found
            
        Raises:
            ValueError: If updates are invalid
            RuntimeError: If database operation fails
        """
        if not updates:
            raise ValueError("No updates provided")
        
        # Validate content length if being updated
        if "content" in updates:
            content = updates["content"]
            if not content or not content.strip():
                raise ValueError("Content cannot be empty")
            if len(content) > settings.max_context_length:
                raise ValueError(f"Content exceeds maximum length of {settings.max_context_length} characters")
        
        try:
            with get_db_context() as db:
                entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
                
                if not entry:
                    return None
                
                # Apply updates
                for field, value in updates.items():
                    if hasattr(entry, field):
                        # Special handling for tags
                        if field == "tags" and value:
                            clean_tags = []
                            for tag in value:
                                if tag and isinstance(tag, str):
                                    clean_tag = tag.strip().lower()
                                    if clean_tag and clean_tag not in clean_tags:
                                        clean_tags.append(clean_tag)
                            setattr(entry, field, clean_tags if clean_tags else None)
                        else:
                            setattr(entry, field, value)
                
                # Update timestamp
                entry.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(entry)
                
                logger.info("Context entry updated", entry_id=entry_id, updates=list(updates.keys()))
                
                return entry
                
        except Exception as e:
            logger.error("Failed to update context entry", entry_id=entry_id, error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to update context entry: {str(e)}")
    
    def delete_context(self, entry_id: str) -> bool:
        """
        Delete a context entry.
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            with get_db_context() as db:
                entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
                
                if not entry:
                    return False
                
                db.delete(entry)
                db.commit()
                
                logger.info("Context entry deleted", entry_id=entry_id)
                
                return True
                
        except Exception as e:
            logger.error("Failed to delete context entry", entry_id=entry_id, error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to delete context entry: {str(e)}")
    
    def search_context(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        context_types: Optional[List[ContextType]] = None,
        tags: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search context entries by content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            context_types: Filter by context types
            tags: Filter by tags
            
        Returns:
            Tuple of (matching_entries_as_dicts, total_count)
        """
        if not query or not query.strip():
            return [], 0
        
        search_term = query.strip()
        
        filters = {
            "search": search_term,
        }
        
        if context_types:
            filters["context_types"] = context_types
        
        if tags:
            filters["tags"] = tags
        
        # Search with relevance ordering (simple approach)
        entries, total = self.get_context(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by="access_count",  # More accessed content is more relevant
            order_desc=True,
        )
        
        return entries, total
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the context vault.
        
        Returns:
            Dictionary with vault statistics
        """
        try:
            with get_db_context() as db:
                # Basic counts
                total_entries = db.query(ContextEntry).count()
                
                # Count by type
                type_counts = db.query(
                    ContextEntry.context_type,
                    func.count(ContextEntry.id)
                ).group_by(ContextEntry.context_type).all()
                
                # Recent activity
                recent_entries = db.query(ContextEntry).filter(
                    ContextEntry.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                # Most accessed
                most_accessed = db.query(ContextEntry).order_by(
                    desc(ContextEntry.access_count)
                ).limit(5).all()
                
                # Total content length
                total_content_length = db.query(
                    func.sum(func.length(ContextEntry.content))
                ).scalar() or 0
                
                # Date range
                oldest_entry = db.query(func.min(ContextEntry.created_at)).scalar()
                newest_entry = db.query(func.max(ContextEntry.created_at)).scalar()
                
                return {
                    "total_entries": total_entries,
                    "entries_by_type": {str(ct): count for ct, count in type_counts},
                    "recent_entries_7d": recent_entries,
                    "most_accessed": [
                        {
                            "id": entry.id,
                            "content_preview": entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                            "access_count": entry.access_count,
                            "context_type": entry.context_type.value,
                        }
                        for entry in most_accessed
                    ],
                    "total_content_length": total_content_length,
                    "average_content_length": total_content_length / total_entries if total_entries > 0 else 0,
                    "date_range": {
                        "oldest": oldest_entry.isoformat() if oldest_entry else None,
                        "newest": newest_entry.isoformat() if newest_entry else None,
                    },
                }
                
        except Exception as e:
            logger.error("Failed to get context stats", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to get context stats: {str(e)}")
    
    def cleanup_old_entries(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old context entries based on retention policy.
        
        Args:
            retention_days: Number of days to retain entries (defaults to config)
            
        Returns:
            Number of entries deleted
        """
        if retention_days is None:
            retention_days = settings.default_context_retention_days
        
        if retention_days <= 0:
            return 0  # No cleanup if retention is disabled
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            with get_db_context() as db:
                # Find old entries
                old_entries = db.query(ContextEntry).filter(
                    ContextEntry.created_at < cutoff_date
                ).all()
                
                count = len(old_entries)
                
                if count > 0:
                    # Delete old entries
                    for entry in old_entries:
                        db.delete(entry)
                    
                    db.commit()
                    
                    logger.info(
                        "Cleaned up old context entries",
                        deleted_count=count,
                        retention_days=retention_days,
                        cutoff_date=cutoff_date.isoformat(),
                    )
                
                return count
                
        except Exception as e:
            logger.error("Failed to cleanup old entries", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to cleanup old entries: {str(e)}")
    
    def export_context(
        self,
        filters: Optional[Dict[str, Any]] = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Export context entries for backup or migration.
        
        Args:
            filters: Filters to apply to export
            format: Export format (json, csv)
            
        Returns:
            Dictionary with export data and metadata
        """
        try:
            entries, total = self.get_context(
                filters=filters,
                limit=10000,  # Large limit for export
                offset=0,
            )
            
            export_data = {
                "metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "total_entries": total,
                    "format": format,
                    "filters_applied": filters or {},
                },
                "entries": [entry.to_dict(include_metadata=True) for entry in entries],
            }
            
            logger.info("Context export completed", total_entries=total, format=format)
            
            return export_data
            
        except Exception as e:
            logger.error("Failed to export context", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to export context: {str(e)}")


# Global vault service instance
vault_service = VaultService()
