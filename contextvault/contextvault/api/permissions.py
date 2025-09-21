"""Permission management API endpoints."""

import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..models import Permission, ContextEntry
from ..schemas import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionSummary,
    PermissionCheck,
    PermissionCheckResult,
    ModelPermissionsSummary,
    BulkPermissionOperation,
    BulkOperationResult,
    SuccessResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get("/", response_model=List[PermissionResponse])
async def get_permissions(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session)
):
    """Get all permission rules with optional filtering."""
    
    query = db.query(Permission)
    
    # Apply filters
    if model_id:
        query = query.filter(Permission.model_id == model_id)
    
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)
    
    # Order by creation date
    query = query.order_by(desc(Permission.created_at))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    permissions = query.all()
    
    return [PermissionResponse.from_orm(perm) for perm in permissions]


@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new permission rule."""
    
    # Check if permission already exists for this model
    existing = db.query(Permission).filter(
        Permission.model_id == permission_data.model_id
    ).first()
    
    if existing:
        # Update existing permission instead of creating duplicate
        for field, value in permission_data.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        
        return PermissionResponse.from_orm(existing)
    
    try:
        # Create new permission
        permission = Permission(
            model_id=permission_data.model_id,
            model_name=permission_data.model_name,
            scope=permission_data.scope,
            rules=permission_data.rules,
            is_active=permission_data.is_active,
            allow_all=permission_data.allow_all,
            deny_all=permission_data.deny_all,
            description=permission_data.description,
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        return PermissionResponse.from_orm(permission)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create permission: {str(e)}")


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    db: Session = Depends(get_db_session)
):
    """Get a specific permission by ID."""
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return PermissionResponse.from_orm(permission)


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    update_data: PermissionUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a specific permission."""
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    try:
        # Update fields that were provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(permission, field, value)
        
        # Update timestamp
        permission.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(permission)
        
        return PermissionResponse.from_orm(permission)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update permission: {str(e)}")


@router.delete("/{permission_id}", response_model=SuccessResponse)
async def delete_permission(
    permission_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete a specific permission."""
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    try:
        model_id = permission.model_id
        db.delete(permission)
        db.commit()
        
        return SuccessResponse(
            message=f"Permission for model '{model_id}' deleted successfully",
            data={"id": permission_id, "model_id": model_id}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete permission: {str(e)}")


@router.post("/check", response_model=PermissionCheckResult)
async def check_permission(
    check_request: PermissionCheck,
    db: Session = Depends(get_db_session)
):
    """Check if a model has permission to access specific content."""
    
    start_time = time.time()
    
    # Get all permissions for this model
    permissions = db.query(Permission).filter(
        and_(
            Permission.model_id == check_request.model_id,
            Permission.is_active == True
        )
    ).all()
    
    if not permissions:
        return PermissionCheckResult(
            allowed=False,
            reason=f"No permissions found for model '{check_request.model_id}'",
            applicable_permissions=[],
            allowed_scopes=[],
            check_time_ms=int((time.time() - start_time) * 1000),
        )
    
    # Check for deny_all permissions first
    for perm in permissions:
        if perm.deny_all:
            perm.record_usage()
            db.commit()
            
            return PermissionCheckResult(
                allowed=False,
                reason="Model has deny_all permission",
                applicable_permissions=[perm.id],
                denied_by="deny_all_rule",
                allowed_scopes=[],
                check_time_ms=int((time.time() - start_time) * 1000),
            )
    
    # Check for allow_all permissions
    for perm in permissions:
        if perm.allow_all:
            perm.record_usage()
            db.commit()
            
            return PermissionCheckResult(
                allowed=True,
                reason="Model has allow_all permission",
                applicable_permissions=[perm.id],
                allowed_scopes=["all"],
                check_time_ms=int((time.time() - start_time) * 1000),
            )
    
    # Check specific scope permissions
    applicable_perms = []
    all_scopes = set()
    
    for perm in permissions:
        scopes = perm.get_allowed_scopes()
        all_scopes.update(scopes)
        applicable_perms.append(perm.id)
        
        # Check if the requested scope is allowed
        if check_request.scope and perm.has_scope(check_request.scope):
            # Additional rule checks
            if check_request.context_entry_id:
                # Get the context entry to check detailed rules
                entry = db.query(ContextEntry).filter(
                    ContextEntry.id == check_request.context_entry_id
                ).first()
                
                if entry:
                    # Check tag restrictions
                    if entry.tags:
                        for tag in entry.tags:
                            if not perm.is_tag_allowed(tag):
                                return PermissionCheckResult(
                                    allowed=False,
                                    reason=f"Tag '{tag}' is not allowed",
                                    applicable_permissions=applicable_perms,
                                    denied_by="tag_restriction",
                                    allowed_scopes=list(all_scopes),
                                    check_time_ms=int((time.time() - start_time) * 1000),
                                )
                    
                    # Check max age
                    max_age_days = perm.get_max_age_days()
                    if max_age_days and not entry.is_recent(max_age_days):
                        return PermissionCheckResult(
                            allowed=False,
                            reason=f"Content is older than {max_age_days} days",
                            applicable_permissions=applicable_perms,
                            denied_by="age_restriction",
                            allowed_scopes=list(all_scopes),
                            check_time_ms=int((time.time() - start_time) * 1000),
                        )
            
            # Check tag filters in request
            if check_request.tags:
                for tag in check_request.tags:
                    if not perm.is_tag_allowed(tag):
                        return PermissionCheckResult(
                            allowed=False,
                            reason=f"Tag '{tag}' is not allowed",
                            applicable_permissions=applicable_perms,
                            denied_by="tag_restriction",
                            allowed_scopes=list(all_scopes),
                            check_time_ms=int((time.time() - start_time) * 1000),
                        )
            
            # Permission granted
            perm.record_usage()
            db.commit()
            
            return PermissionCheckResult(
                allowed=True,
                reason=f"Model has permission for scope '{check_request.scope}'",
                applicable_permissions=applicable_perms,
                allowed_scopes=list(all_scopes),
                check_time_ms=int((time.time() - start_time) * 1000),
            )
    
    # No specific permission found
    return PermissionCheckResult(
        allowed=False,
        reason=f"No permission found for requested scope '{check_request.scope}'",
        applicable_permissions=applicable_perms,
        allowed_scopes=list(all_scopes),
        check_time_ms=int((time.time() - start_time) * 1000),
    )


@router.get("/models/{model_id}/summary", response_model=ModelPermissionsSummary)
async def get_model_permissions_summary(
    model_id: str,
    db: Session = Depends(get_db_session)
):
    """Get a summary of all permissions for a specific model."""
    
    permissions = db.query(Permission).filter(Permission.model_id == model_id).all()
    
    if not permissions:
        raise HTTPException(status_code=404, detail=f"No permissions found for model '{model_id}'")
    
    total_permissions = len(permissions)
    active_permissions = len([p for p in permissions if p.is_active])
    
    # Collect all scopes
    all_scopes = set()
    has_unrestricted = False
    is_denied = False
    total_usage = 0
    last_used = None
    
    for perm in permissions:
        if perm.is_active:
            if perm.allow_all:
                has_unrestricted = True
                all_scopes.add("all")
            elif perm.deny_all:
                is_denied = True
            else:
                all_scopes.update(perm.get_allowed_scopes())
        
        total_usage += perm.usage_count or 0
        
        if perm.last_used_at:
            if not last_used or perm.last_used_at > last_used:
                last_used = perm.last_used_at
    
    # Get model name (use the most recent one)
    model_name = None
    for perm in sorted(permissions, key=lambda p: p.updated_at, reverse=True):
        if perm.model_name:
            model_name = perm.model_name
            break
    
    return ModelPermissionsSummary(
        model_id=model_id,
        model_name=model_name,
        total_permissions=total_permissions,
        active_permissions=active_permissions,
        allowed_scopes=list(all_scopes),
        has_unrestricted_access=has_unrestricted,
        is_denied_access=is_denied,
        last_used=last_used,
        usage_count=total_usage,
    )


@router.get("/models/", response_model=List[ModelPermissionsSummary])
async def get_all_model_permissions(
    include_inactive: bool = Query(False, description="Include inactive permissions"),
    db: Session = Depends(get_db_session)
):
    """Get permission summaries for all models."""
    
    query = db.query(Permission.model_id).distinct()
    
    if not include_inactive:
        query = query.filter(Permission.is_active == True)
    
    model_ids = [result[0] for result in query.all()]
    
    summaries = []
    for model_id in model_ids:
        try:
            summary = await get_model_permissions_summary(model_id, db)
            summaries.append(summary)
        except HTTPException:
            # Skip models that don't have permissions (shouldn't happen with our query)
            continue
    
    return summaries


@router.post("/bulk", response_model=BulkOperationResult)
async def bulk_permission_operation(
    operation: BulkPermissionOperation,
    db: Session = Depends(get_db_session)
):
    """Perform bulk operations on permissions."""
    
    start_time = time.time()
    
    try:
        # Get permissions to operate on
        if operation.permission_ids:
            permissions = db.query(Permission).filter(
                Permission.id.in_(operation.permission_ids)
            ).all()
        elif operation.model_ids:
            permissions = db.query(Permission).filter(
                Permission.model_id.in_(operation.model_ids)
            ).all()
        else:
            raise HTTPException(status_code=400, detail="Either permission_ids or model_ids must be provided")
        
        if not permissions:
            raise HTTPException(status_code=404, detail="No permissions found")
        
        successful = 0
        failed = 0
        errors = []
        
        for perm in permissions:
            try:
                if operation.operation == "activate":
                    perm.is_active = True
                    perm.updated_at = datetime.utcnow()
                    successful += 1
                
                elif operation.operation == "deactivate":
                    perm.is_active = False
                    perm.updated_at = datetime.utcnow()
                    successful += 1
                
                elif operation.operation == "delete":
                    db.delete(perm)
                    successful += 1
                
                elif operation.operation == "update_scope":
                    new_scope = operation.parameters.get("scope")
                    if new_scope:
                        perm.scope = new_scope
                        perm.updated_at = datetime.utcnow()
                        successful += 1
                    else:
                        errors.append(f"No scope specified for permission {perm.id}")
                        failed += 1
                
                elif operation.operation == "add_scope":
                    scope_to_add = operation.parameters.get("scope")
                    if scope_to_add:
                        perm.add_scope(scope_to_add)
                        perm.updated_at = datetime.utcnow()
                        successful += 1
                    else:
                        errors.append(f"No scope specified for permission {perm.id}")
                        failed += 1
                
                elif operation.operation == "remove_scope":
                    scope_to_remove = operation.parameters.get("scope")
                    if scope_to_remove:
                        perm.remove_scope(scope_to_remove)
                        perm.updated_at = datetime.utcnow()
                        successful += 1
                    else:
                        errors.append(f"No scope specified for permission {perm.id}")
                        failed += 1
                
                elif operation.operation == "reset_usage":
                    perm.usage_count = 0
                    perm.last_used_at = None
                    perm.updated_at = datetime.utcnow()
                    successful += 1
                
                else:
                    errors.append(f"Unknown operation: {operation.operation}")
                    failed += 1
                    
            except Exception as e:
                errors.append(f"Error processing permission {perm.id}: {str(e)}")
                failed += 1
        
        # Commit all changes
        db.commit()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        total_requested = len(operation.permission_ids or []) + len(operation.model_ids or [])
        
        return BulkOperationResult(
            operation=operation.operation,
            total_requested=total_requested,
            successful=successful,
            failed=failed,
            errors=errors,
            processing_time_ms=processing_time_ms,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Bulk operation failed: {str(e)}")


@router.post("/models/{model_id}/reset", response_model=SuccessResponse)
async def reset_model_permissions(
    model_id: str,
    scope: str = Query("basic", description="Default scope to assign"),
    db: Session = Depends(get_db_session)
):
    """Reset permissions for a model to default settings."""
    
    try:
        # Delete existing permissions
        existing_permissions = db.query(Permission).filter(Permission.model_id == model_id).all()
        for perm in existing_permissions:
            db.delete(perm)
        
        # Create default permission
        default_permission = Permission.create_default_permission(model_id, scope)
        db.add(default_permission)
        
        db.commit()
        
        return SuccessResponse(
            message=f"Permissions for model '{model_id}' reset to default",
            data={
                "model_id": model_id,
                "default_scope": scope,
                "permission_id": default_permission.id
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to reset permissions: {str(e)}")
