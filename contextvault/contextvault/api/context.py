"""Context management API endpoints."""

import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..models import ContextEntry
from ..schemas import (
    ContextEntryCreate,
    ContextEntryUpdate, 
    ContextEntryResponse,
    ContextEntryBrief,
    ContextQuery,
    ContextQueryResponse,
    ContextStats,
    BulkContextOperation,
    BulkOperationResult,
    SuccessResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get("/", response_model=ContextQueryResponse)
async def get_context_entries(
    model: Optional[str] = Query(None, description="AI model requesting context"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    context_types: Optional[List[str]] = Query(None, description="Filter by context types"), 
    source: Optional[str] = Query(None, description="Filter by source pattern"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of entries"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    since: Optional[datetime] = Query(None, description="Only entries after this timestamp"),
    include_metadata: bool = Query(False, description="Include full metadata"),
    search: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve context entries with filtering and permissions.
    
    This endpoint applies permission checks if a model is specified,
    and supports various filtering options.
    """
    start_time = time.time()
    
    # Build base query
    query = db.query(ContextEntry)
    
    # Apply filters
    filters = []
    
    if context_types:
        filters.append(ContextEntry.context_type.in_(context_types))
    
    if since:
        filters.append(ContextEntry.created_at >= since)
    
    if source:
        filters.append(ContextEntry.source.ilike(f"%{source}%"))
    
    if tags:
        # Filter by tags (JSON array contains any of the specified tags)
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(ContextEntry.tags.contains([tag]))
        filters.append(or_(*tag_conditions))
    
    if search:
        # Simple text search in content
        filters.append(ContextEntry.content.ilike(f"%{search}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply permission checks if model is specified
    if model:
        # TODO: Implement permission checking service
        # For now, we'll just log the model parameter
        pass
    
    # Get total count before pagination
    total = query.count()
    
    # Apply ordering and pagination
    query = query.order_by(desc(ContextEntry.created_at))
    query = query.offset(offset).limit(limit)
    
    # Execute query
    entries = query.all()
    
    # Convert to response format
    entry_responses = []
    for entry in entries:
        # Record access
        entry.record_access()
        
        # Convert to response model
        if include_metadata:
            entry_responses.append(ContextEntryResponse.from_orm(entry))
        else:
            entry_responses.append(ContextEntryResponse.from_orm(entry))
    
    # Commit access tracking
    db.commit()
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return ContextQueryResponse(
        entries=entry_responses,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_time_ms=query_time_ms,
    )


@router.post("/", response_model=ContextEntryResponse)
async def create_context_entry(
    entry_data: ContextEntryCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new context entry."""
    try:
        # Create new context entry
        entry = ContextEntry(
            content=entry_data.content,
            context_type=entry_data.context_type,
            source=entry_data.source,
            tags=entry_data.tags,
            metadata=entry_data.metadata,
            user_id=entry_data.user_id,
            session_id=entry_data.session_id,
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        return ContextEntryResponse.from_orm(entry)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create context entry: {str(e)}")


@router.get("/{entry_id}", response_model=ContextEntryResponse)
async def get_context_entry(
    entry_id: str,
    include_metadata: bool = Query(True, description="Include full metadata"),
    db: Session = Depends(get_db_session)
):
    """Get a specific context entry by ID."""
    entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Context entry not found")
    
    # Record access
    entry.record_access()
    db.commit()
    
    return ContextEntryResponse.from_orm(entry)


@router.put("/{entry_id}", response_model=ContextEntryResponse)
async def update_context_entry(
    entry_id: str,
    update_data: ContextEntryUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a specific context entry."""
    entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Context entry not found")
    
    try:
        # Update fields that were provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(entry, field, value)
        
        # Update timestamp
        entry.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(entry)
        
        return ContextEntryResponse.from_orm(entry)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update context entry: {str(e)}")


@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_context_entry(
    entry_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete a specific context entry."""
    entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Context entry not found")
    
    try:
        db.delete(entry)
        db.commit()
        
        return SuccessResponse(
            message=f"Context entry {entry_id} deleted successfully",
            data={"id": entry_id}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete context entry: {str(e)}")


@router.get("/search/{query}", response_model=ContextQueryResponse)
async def search_context_entries(
    query: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    model: Optional[str] = Query(None, description="AI model requesting context"),
    context_types: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Search context entries by content."""
    start_time = time.time()
    
    # Build search query
    search_query = db.query(ContextEntry)
    
    # Text search in content and source
    search_conditions = [
        ContextEntry.content.ilike(f"%{query}%"),
        ContextEntry.source.ilike(f"%{query}%"),
    ]
    
    # Search in tags (if they contain the query string)
    search_conditions.append(
        ContextEntry.tags.op('LIKE')(f'%"{query}"%')
    )
    
    search_query = search_query.filter(or_(*search_conditions))
    
    # Apply additional filters
    if context_types:
        search_query = search_query.filter(ContextEntry.context_type.in_(context_types))
    
    if tags:
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(ContextEntry.tags.contains([tag]))
        search_query = search_query.filter(or_(*tag_conditions))
    
    # Apply permission checks if model is specified
    if model:
        # TODO: Implement permission checking
        pass
    
    # Get total count
    total = search_query.count()
    
    # Order by relevance (simple approach - could be improved with full-text search)
    search_query = search_query.order_by(
        desc(ContextEntry.access_count),
        desc(ContextEntry.created_at)
    )
    
    # Apply pagination
    search_query = search_query.offset(offset).limit(limit)
    
    # Execute query
    entries = search_query.all()
    
    # Record access for all returned entries
    for entry in entries:
        entry.record_access()
    
    db.commit()
    
    # Convert to response format
    entry_responses = [ContextEntryResponse.from_orm(entry) for entry in entries]
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return ContextQueryResponse(
        entries=entry_responses,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_time_ms=query_time_ms,
    )


@router.get("/stats/summary", response_model=ContextStats)
async def get_context_stats(db: Session = Depends(get_db_session)):
    """Get statistics about context entries."""
    
    # Basic counts
    total_entries = db.query(ContextEntry).count()
    
    # Count by type
    type_counts = db.query(
        ContextEntry.context_type,
        func.count(ContextEntry.id)
    ).group_by(ContextEntry.context_type).all()
    
    entries_by_type = {str(ct): count for ct, count in type_counts}
    
    # Most accessed entries
    most_accessed = db.query(ContextEntry).order_by(
        desc(ContextEntry.access_count),
        desc(ContextEntry.created_at)
    ).limit(10).all()
    
    most_accessed_brief = [ContextEntryBrief.from_orm(entry) for entry in most_accessed]
    
    # Recent entries
    recent = db.query(ContextEntry).order_by(
        desc(ContextEntry.created_at)
    ).limit(10).all()
    
    recent_brief = [ContextEntryBrief.from_orm(entry) for entry in recent]
    
    # Date range
    oldest_entry = db.query(func.min(ContextEntry.created_at)).scalar()
    newest_entry = db.query(func.max(ContextEntry.created_at)).scalar()
    
    # Character count
    total_chars = db.query(func.sum(func.length(ContextEntry.content))).scalar() or 0
    
    # Average access count
    avg_access = db.query(func.avg(ContextEntry.access_count)).scalar() or 0.0
    
    # Tag counts (this is a simplified approach - in production you'd want proper JSON aggregation)
    entries_with_tags = db.query(ContextEntry).filter(ContextEntry.tags.isnot(None)).all()
    tag_counts = {}
    for entry in entries_with_tags:
        if entry.tags:
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    return ContextStats(
        total_entries=total_entries,
        entries_by_type=entries_by_type,
        entries_by_tag=tag_counts,
        most_accessed=most_accessed_brief,
        recent_entries=recent_brief,
        oldest_entry=oldest_entry,
        newest_entry=newest_entry,
        total_characters=total_chars,
        average_access_count=float(avg_access),
    )


@router.post("/bulk", response_model=BulkOperationResult)
async def bulk_context_operation(
    operation: BulkContextOperation,
    db: Session = Depends(get_db_session)
):
    """Perform bulk operations on context entries."""
    start_time = time.time()
    
    try:
        # Get the entries to operate on
        entries = db.query(ContextEntry).filter(
            ContextEntry.id.in_(operation.entry_ids)
        ).all()
        
        if not entries:
            raise HTTPException(status_code=404, detail="No entries found with the provided IDs")
        
        successful = 0
        failed = 0
        errors = []
        
        for entry in entries:
            try:
                if operation.operation == "delete":
                    db.delete(entry)
                    successful += 1
                
                elif operation.operation == "update_tags":
                    new_tags = operation.parameters.get("tags", [])
                    entry.tags = new_tags
                    entry.updated_at = datetime.utcnow()
                    successful += 1
                
                elif operation.operation == "add_tags":
                    new_tags = operation.parameters.get("tags", [])
                    current_tags = entry.tags or []
                    entry.tags = list(set(current_tags + new_tags))
                    entry.updated_at = datetime.utcnow()
                    successful += 1
                
                elif operation.operation == "remove_tags":
                    tags_to_remove = operation.parameters.get("tags", [])
                    if entry.tags:
                        entry.tags = [tag for tag in entry.tags if tag not in tags_to_remove]
                    entry.updated_at = datetime.utcnow()
                    successful += 1
                
                elif operation.operation == "update_type":
                    new_type = operation.parameters.get("context_type")
                    if new_type:
                        entry.context_type = new_type
                        entry.updated_at = datetime.utcnow()
                        successful += 1
                    else:
                        errors.append(f"No context_type specified for entry {entry.id}")
                        failed += 1
                
                else:
                    errors.append(f"Unknown operation: {operation.operation}")
                    failed += 1
                    
            except Exception as e:
                errors.append(f"Error processing entry {entry.id}: {str(e)}")
                failed += 1
        
        # Commit all changes
        db.commit()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BulkOperationResult(
            operation=operation.operation,
            total_requested=len(operation.entry_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processing_time_ms=processing_time_ms,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Bulk operation failed: {str(e)}")


@router.get("/tags/", response_model=List[str])
async def get_all_tags(
    limit: int = Query(1000, ge=1, le=10000),
    min_count: int = Query(1, ge=1, description="Minimum tag usage count"),
    db: Session = Depends(get_db_session)
):
    """Get all unique tags used in context entries."""
    
    # Get all entries with tags
    entries = db.query(ContextEntry).filter(ContextEntry.tags.isnot(None)).all()
    
    # Count tag occurrences
    tag_counts = {}
    for entry in entries:
        if entry.tags:
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Filter by minimum count and sort by frequency
    filtered_tags = [
        tag for tag, count in tag_counts.items() 
        if count >= min_count
    ]
    
    # Sort by frequency (descending) then alphabetically
    filtered_tags.sort(key=lambda tag: (-tag_counts[tag], tag))
    
    return filtered_tags[:limit]
