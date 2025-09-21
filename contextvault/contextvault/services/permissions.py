"""Permission checking and management service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from ..database import get_db_context
from ..models import Permission, ContextEntry, ContextType
from ..config import settings

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing and checking AI model permissions."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the permission service."""
        self.db_session = db_session
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_db_context())
    
    def check_permission(
        self,
        model_id: str,
        context_entry: ContextEntry,
        requested_action: str = "read",
    ) -> Tuple[bool, str, List[str]]:
        """
        Check if a model has permission to access a context entry.
        
        Args:
            model_id: The AI model identifier
            context_entry: The context entry to check access for
            requested_action: The action being requested (read, write, delete)
            
        Returns:
            Tuple of (allowed, reason, applicable_permission_ids)
        """
        try:
            with get_db_context() as db:
                # Get active permissions for this model
                permissions = db.query(Permission).filter(
                    and_(
                        Permission.model_id == model_id,
                        Permission.is_active == True
                    )
                ).all()
                
                if not permissions:
                    # No permissions found - check if unknown models are allowed
                    if settings.allow_unknown_models:
                        logger.info(f"Unknown model allowed by default: {model_id}")
                        return True, "Unknown model allowed by default configuration", []
                    else:
                        logger.warning(f"No permissions found for model: {model_id}")
                        return False, f"No permissions configured for model '{model_id}'", []
                
                # Check for explicit deny_all first
                deny_permissions = [p for p in permissions if p.deny_all]
                if deny_permissions:
                    perm_ids = [p.id for p in deny_permissions]
                    for perm in deny_permissions:
                        perm.record_usage()
                    db.commit()
                    
                    logger.info(f"Access denied by deny_all rule for model {model_id}, permissions {perm_ids}")
                    return False, "Access denied by explicit deny rule", perm_ids
                
                # Check for allow_all permissions
                allow_all_permissions = [p for p in permissions if p.allow_all]
                if allow_all_permissions:
                    perm_ids = [p.id for p in allow_all_permissions]
                    for perm in allow_all_permissions:
                        perm.record_usage()
                    db.commit()
                    
                    logger.info(f"Access granted by allow_all rule for model {model_id}, permissions {perm_ids}")
                    return True, "Access granted by unrestricted permission", perm_ids
                
                # Check specific permissions
                applicable_permissions = []
                
                for permission in permissions:
                    # Check if this permission applies to the context entry
                    if self._permission_applies_to_entry(permission, context_entry):
                        applicable_permissions.append(permission)
                
                if not applicable_permissions:
                    logger.info(f"No applicable permissions found for model {model_id}, entry {context_entry.id}")
                    return False, "No applicable permissions found for this content", []
                
                # Evaluate the most permissive applicable permission
                for permission in applicable_permissions:
                    allowed, reason = self._evaluate_permission_rules(permission, context_entry, requested_action)
                    
                    if allowed:
                        permission.record_usage()
                        db.commit()
                        
                        logger.info(f"Access granted for model {model_id} to entry {context_entry.id}: {reason}")
                        return True, reason, [permission.id]
                
                # No permission granted access
                perm_ids = [p.id for p in applicable_permissions]
                logger.info(f"Access denied by permission rules for model {model_id}, entry {context_entry.id}")
                return False, "Access denied by permission rules", perm_ids
                
        except Exception as e:
            logger.error(f"Error checking permission for model {model_id}: {str(e)}", exc_info=True)
            return False, f"Permission check failed: {str(e)}", []
    
    def _permission_applies_to_entry(self, permission: Permission, context_entry: ContextEntry) -> bool:
        """Check if a permission rule applies to a context entry."""
        
        # Check scope (context type mapping)
        allowed_scopes = permission.get_allowed_scopes()
        
        # Map context types to scopes
        context_type_scope_map = {
            ContextType.TEXT: "text",
            ContextType.FILE: "files",
            ContextType.EVENT: "events", 
            ContextType.PREFERENCE: "preferences",
            ContextType.NOTE: "notes",
            ContextType.PERSONAL_INFO: "personal",
            ContextType.GOAL: "goals",
            ContextType.RELATIONSHIP: "relationships",
            ContextType.SKILL: "skills",
            ContextType.PROJECT: "projects",
        }
        
        entry_scope = context_type_scope_map.get(context_entry.context_type, "text")
        
        # Check if the entry's scope is allowed
        # Handle both enum and string context_type
        context_type_value = (
            context_entry.context_type.value 
            if hasattr(context_entry.context_type, 'value') 
            else context_entry.context_type
        )
        
        scope_allowed = (
            "all" in allowed_scopes or
            entry_scope in allowed_scopes or
            context_type_value in allowed_scopes
        )
        
        if not scope_allowed:
            return False
        
        # Check tag restrictions
        if context_entry.tags:
            for tag in context_entry.tags:
                if not permission.is_tag_allowed(tag):
                    return False
        
        # Check age restrictions
        max_age_days = permission.get_max_age_days()
        if max_age_days and not context_entry.is_recent(max_age_days):
            return False
        
        return True
    
    def _evaluate_permission_rules(
        self,
        permission: Permission,
        context_entry: ContextEntry,
        requested_action: str,
    ) -> Tuple[bool, str]:
        """Evaluate specific permission rules for a context entry."""
        
        # Check action-specific rules
        rules = permission.rules or {}
        
        # Check read permissions (default action)
        if requested_action == "read":
            # Basic read access is allowed if we got this far
            pass
        elif requested_action == "write":
            # Check if writing is allowed
            if not rules.get("allow_write", False):
                return False, "Write access not permitted"
        elif requested_action == "delete":
            # Check if deletion is allowed
            if not rules.get("allow_delete", False):
                return False, "Delete access not permitted"
        
        # Check content length restrictions
        max_content_length = rules.get("max_content_length")
        if max_content_length and len(context_entry.content) > max_content_length:
            return False, f"Content exceeds maximum allowed length of {max_content_length} characters"
        
        # Check source restrictions
        allowed_sources = rules.get("allowed_sources")
        if allowed_sources and context_entry.source:
            if not any(source in context_entry.source for source in allowed_sources):
                return False, "Content source not allowed"
        
        blocked_sources = rules.get("blocked_sources")
        if blocked_sources and context_entry.source:
            if any(source in context_entry.source for source in blocked_sources):
                return False, "Content source is blocked"
        
        return True, "Access granted by permission rules"
    
    def get_allowed_scopes(self, model_id: str) -> List[str]:
        """
        Get all allowed scopes for a model.
        
        Args:
            model_id: The AI model identifier
            
        Returns:
            List of allowed scopes
        """
        try:
            with get_db_context() as db:
                permissions = db.query(Permission).filter(
                    and_(
                        Permission.model_id == model_id,
                        Permission.is_active == True
                    )
                ).all()
                
                if not permissions:
                    return [] if not settings.allow_unknown_models else ["basic"]
                
                all_scopes = set()
                
                for permission in permissions:
                    if permission.deny_all:
                        return []  # Deny all overrides everything
                    elif permission.allow_all:
                        return ["all"]  # Allow all is maximum permission
                    else:
                        all_scopes.update(permission.get_allowed_scopes())
                
                return list(all_scopes)
                
        except Exception as e:
            logger.error(f"Error getting allowed scopes for model {model_id}: {str(e)}", exc_info=True)
            return []
    
    def create_permission_rule(
        self,
        model_id: str,
        scopes: List[str],
        rules: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Permission:
        """
        Create a new permission rule for a model.
        
        Args:
            model_id: The AI model identifier
            scopes: List of allowed scopes
            rules: Additional permission rules
            description: Human-readable description
            model_name: Human-readable model name
            
        Returns:
            The created Permission object
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If database operation fails
        """
        if not model_id or not model_id.strip():
            raise ValueError("Model ID cannot be empty")
        
        if not scopes:
            raise ValueError("At least one scope must be specified")
        
        try:
            db = self._get_session()
            # Check if permission already exists
            existing = db.query(Permission).filter(Permission.model_id == model_id).first()
            
            if existing:
                # Update existing permission
                existing.scope = ",".join(scopes)
                existing.rules = rules or {}
                existing.description = description
                existing.model_name = model_name
                existing.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing)
                
                logger.info(f"Permission rule updated: model_id={model_id}, scopes={scopes}")
                return existing
            else:
                # Create new permission
                permission = Permission(
                    model_id=model_id.strip(),
                    model_name=model_name,
                    scope=",".join(scopes),
                    rules=rules or {},
                    description=description,
                )
                
                db.add(permission)
                db.commit()
                db.refresh(permission)
                
                logger.info(f"Permission rule created: model_id={model_id}, scopes={scopes}, permission_id={permission.id}")
                return permission
                    
        except Exception as e:
            logger.error(f"Failed to create permission rule: model_id={model_id}, error={str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to create permission rule: {str(e)}")
    
    def apply_permission_filters(
        self,
        context_entries: List[ContextEntry],
        model_id: str,
    ) -> List[ContextEntry]:
        """
        Filter context entries based on model permissions.
        
        Args:
            context_entries: List of context entries to filter
            model_id: The AI model identifier
            
        Returns:
            Filtered list of context entries the model can access
        """
        if not context_entries:
            return []
        
        try:
            with get_db_context() as db:
                # Get permissions for the model
                permissions = db.query(Permission).filter(
                    and_(
                        Permission.model_id == model_id,
                        Permission.is_active == True
                    )
                ).all()
                
                print(f"[PERMISSION DEBUG] Found {len(permissions)} permissions for model {model_id}")
                for p in permissions:
                    print(f"[PERMISSION DEBUG] Permission: allow_all={p.allow_all}, deny_all={p.deny_all}, scope={p.scope}, rules={p.rules}")
                
                if not permissions:
                    print(f"[PERMISSION DEBUG] No permissions found for model {model_id}")
                    print(f"[PERMISSION DEBUG] allow_unknown_models setting: {settings.allow_unknown_models}")
                    if settings.allow_unknown_models:
                        print(f"[PERMISSION DEBUG] Allowing basic access for unknown model {model_id}")
                        # Allow basic access for unknown models
                        return context_entries
                    else:
                        print(f"[PERMISSION DEBUG] Denying access for unknown model {model_id}")
                        logger.warning(f"No permissions for model, filtering all content: {model_id}")
                        return []
                
                # Check for deny_all
                if any(p.deny_all for p in permissions):
                    logger.info(f"Model has deny_all permission, filtering all content: {model_id}")
                    return []
                
                # Check for allow_all
                if any(p.allow_all for p in permissions):
                    logger.info(f"Model has allow_all permission, allowing all content: {model_id}")
                    return context_entries
                
                # Filter entries based on permissions
                allowed_entries = []
                
                for entry in context_entries:
                    allowed, reason, perm_ids = self.check_permission(model_id, entry)
                    if allowed:
                        allowed_entries.append(entry)
                
                logger.info(f"Applied permission filters for model {model_id}: {len(allowed_entries)}/{len(context_entries)} entries allowed")
                
                return allowed_entries
                
        except Exception as e:
            logger.error(f"Error applying permission filters for model {model_id}: {str(e)}", exc_info=True)
            # Fail safe - return no entries if there's an error
            return []
    
    def get_permission_summary(self, model_id: str) -> Dict[str, Any]:
        """
        Get a summary of permissions for a model.
        
        Args:
            model_id: The AI model identifier
            
        Returns:
            Dictionary with permission summary
        """
        try:
            with get_db_context() as db:
                permissions = db.query(Permission).filter(Permission.model_id == model_id).all()
                
                if not permissions:
                    return {
                        "model_id": model_id,
                        "has_permissions": False,
                        "total_permissions": 0,
                        "active_permissions": 0,
                        "allowed_scopes": [] if not settings.allow_unknown_models else ["basic"],
                        "access_level": "none" if not settings.allow_unknown_models else "basic",
                        "restrictions": [],
                    }
                
                active_permissions = [p for p in permissions if p.is_active]
                
                # Determine access level
                if any(p.deny_all for p in active_permissions):
                    access_level = "none"
                elif any(p.allow_all for p in active_permissions):
                    access_level = "unlimited"
                else:
                    access_level = "limited"
                
                # Collect all scopes
                all_scopes = set()
                restrictions = []
                
                for perm in active_permissions:
                    if not perm.deny_all and not perm.allow_all:
                        all_scopes.update(perm.get_allowed_scopes())
                        
                        # Collect restrictions
                        if perm.get_max_entries():
                            restrictions.append(f"Max {perm.get_max_entries()} entries")
                        
                        if perm.get_max_age_days():
                            restrictions.append(f"Max {perm.get_max_age_days()} days old")
                        
                        excluded_tags = perm.get_excluded_tags()
                        if excluded_tags:
                            restrictions.append(f"Excludes tags: {', '.join(excluded_tags)}")
                        
                        allowed_tags = perm.get_allowed_tags()
                        if allowed_tags:
                            restrictions.append(f"Only tags: {', '.join(allowed_tags)}")
                
                return {
                    "model_id": model_id,
                    "has_permissions": True,
                    "total_permissions": len(permissions),
                    "active_permissions": len(active_permissions),
                    "allowed_scopes": list(all_scopes),
                    "access_level": access_level,
                    "restrictions": restrictions,
                    "last_used": max(
                        (p.last_used_at for p in permissions if p.last_used_at),
                        default=None
                    ),
                    "total_usage": sum(p.usage_count or 0 for p in permissions),
                }
                
        except Exception as e:
            logger.error(f"Error getting permission summary for model {model_id}: {str(e)}", exc_info=True)
            return {
                "model_id": model_id,
                "has_permissions": False,
                "error": str(e),
            }
    
    def validate_model_access(
        self,
        model_id: str,
        context_query: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate that a model can perform a specific context query.
        
        Args:
            model_id: The AI model identifier
            context_query: The query parameters to validate
            
        Returns:
            Tuple of (allowed, reason, modified_query)
        """
        try:
            # Get allowed scopes for the model
            allowed_scopes = self.get_allowed_scopes(model_id)
            
            if not allowed_scopes:
                return False, "No access permissions for this model", {}
            
            if "all" in allowed_scopes:
                return True, "Unlimited access granted", context_query
            
            # Validate and modify query based on permissions
            modified_query = context_query.copy()
            
            # Filter context types based on scope
            requested_types = context_query.get("context_types", [])
            if requested_types:
                # Map scopes to context types
                scope_type_map = {
                    "text": [ContextType.TEXT],
                    "files": [ContextType.FILE],
                    "events": [ContextType.EVENT],
                    "preferences": [ContextType.PREFERENCE],
                    "notes": [ContextType.NOTE],
                }
                
                allowed_types = []
                for scope in allowed_scopes:
                    if scope in scope_type_map:
                        allowed_types.extend(scope_type_map[scope])
                
                # Filter requested types
                filtered_types = [t for t in requested_types if t in allowed_types]
                
                if not filtered_types:
                    return False, "No allowed context types in request", {}
                
                modified_query["context_types"] = filtered_types
            
            # Apply permission limits
            with get_db_context() as db:
                permissions = db.query(Permission).filter(
                    and_(
                        Permission.model_id == model_id,
                        Permission.is_active == True
                    )
                ).all()
                
                # Apply most restrictive limits
                max_entries = None
                for perm in permissions:
                    perm_max = perm.get_max_entries()
                    if perm_max:
                        if max_entries is None or perm_max < max_entries:
                            max_entries = perm_max
                
                if max_entries:
                    query_limit = modified_query.get("limit", 50)
                    modified_query["limit"] = min(query_limit, max_entries)
            
            return True, "Query validated and modified based on permissions", modified_query
            
        except Exception as e:
            logger.error(f"Error validating model access for model {model_id}: {str(e)}", exc_info=True)
            return False, f"Access validation failed: {str(e)}", {}


# Global permission service instance
permission_service = PermissionService()
