"""SQLAlchemy models for permission management."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Permission(Base):
    """
    Model for storing AI model permissions.
    
    Controls what context each AI model can access based on scopes,
    rules, and other access control mechanisms.
    """
    
    __tablename__ = "permissions"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the permission rule"
    )
    
    # Model identification
    model_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        index=True,
        comment="Identifier for the AI model (e.g., 'llama2', 'codellama')"
    )
    
    model_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="Human-readable name for the model"
    )
    
    # Basic scope control
    scope: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Comma-separated list of allowed scopes (e.g., 'preferences,notes')"
    )
    
    # Advanced rule-based permissions
    rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Detailed permission rules as JSON"
    )
    
    # Access control flags
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Whether this permission rule is currently active"
    )
    
    allow_all: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether this model has unrestricted access"
    )
    
    deny_all: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether this model is completely denied access"
    )
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Human-readable description of what this permission allows"
    )
    
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="Who created this permission rule"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the permission was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        comment="When the permission was last updated"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When this permission was last used for access control"
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of times this permission has been checked"
    )
    
    def __repr__(self) -> str:
        """String representation of the permission."""
        return (
            f"<Permission(id='{self.id}', "
            f"model_id='{self.model_id}', "
            f"scope='{self.scope}', "
            f"active={self.is_active})>"
        )
    
    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert the permission to a dictionary.
        
        Args:
            include_metadata: Whether to include metadata fields
            
        Returns:
            Dictionary representation of the permission
        """
        result = {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "scope": self.scope,
            "rules": self.rules or {},
            "is_active": self.is_active,
            "allow_all": self.allow_all,
            "deny_all": self.deny_all,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_metadata:
            result.update({
                "created_by": self.created_by,
                "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
                "usage_count": self.usage_count,
            })
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Permission":
        """
        Create a Permission from a dictionary.
        
        Args:
            data: Dictionary containing permission data
            
        Returns:
            New Permission instance
        """
        # Handle datetime conversion
        for field in ["created_at", "updated_at", "last_used_at"]:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def get_allowed_scopes(self) -> List[str]:
        """Get the list of allowed scopes for this permission."""
        if self.allow_all:
            return ["all"]
        if self.deny_all or not self.scope:
            return []
        
        # Parse comma-separated scopes
        scopes = [s.strip() for s in self.scope.split(",") if s.strip()]
        return scopes
    
    def has_scope(self, scope: str) -> bool:
        """Check if this permission includes a specific scope."""
        if not self.is_active:
            return False
        if self.deny_all:
            return False
        if self.allow_all:
            return True
        
        allowed_scopes = self.get_allowed_scopes()
        return scope in allowed_scopes or "all" in allowed_scopes
    
    def add_scope(self, scope: str) -> None:
        """Add a scope to this permission."""
        if self.deny_all:
            return  # Cannot add scopes to denied permission
        
        current_scopes = self.get_allowed_scopes()
        if scope not in current_scopes:
            current_scopes.append(scope)
            self.scope = ",".join(current_scopes)
    
    def remove_scope(self, scope: str) -> bool:
        """
        Remove a scope from this permission.
        
        Returns:
            True if scope was removed, False if scope wasn't present
        """
        current_scopes = self.get_allowed_scopes()
        if scope in current_scopes:
            current_scopes.remove(scope)
            self.scope = ",".join(current_scopes)
            return True
        return False
    
    def get_rule(self, key: str, default: Any = None) -> Any:
        """Get a specific rule value."""
        if not self.rules:
            return default
        return self.rules.get(key, default)
    
    def set_rule(self, key: str, value: Any) -> None:
        """Set a specific rule value."""
        if self.rules is None:
            self.rules = {}
        self.rules[key] = value
    
    def get_max_entries(self) -> Optional[int]:
        """Get the maximum number of context entries this model can access."""
        return self.get_rule("max_entries")
    
    def get_allowed_tags(self) -> Optional[List[str]]:
        """Get the list of allowed tags for this model."""
        return self.get_rule("allowed_tags")
    
    def get_excluded_tags(self) -> Optional[List[str]]:
        """Get the list of excluded tags for this model."""
        return self.get_rule("excluded_tags")
    
    def get_max_age_days(self) -> Optional[int]:
        """Get the maximum age in days for context entries this model can access."""
        return self.get_rule("max_age_days")
    
    def is_tag_allowed(self, tag: str) -> bool:
        """Check if a specific tag is allowed by this permission."""
        allowed_tags = self.get_allowed_tags()
        excluded_tags = self.get_excluded_tags()
        
        # Check exclusions first
        if excluded_tags and tag in excluded_tags:
            return False
        
        # If no allowed tags specified, allow all (except excluded)
        if not allowed_tags:
            return True
        
        # Check if tag is in allowed list
        return tag in allowed_tags
    
    def record_usage(self) -> None:
        """Record that this permission was used for access control."""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used_at = datetime.utcnow()
    
    def validate_rules(self) -> List[str]:
        """
        Validate the permission rules and return any issues.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not self.rules:
            return errors
        
        # Check max_entries
        max_entries = self.get_rule("max_entries")
        if max_entries is not None:
            if not isinstance(max_entries, int) or max_entries < 0:
                errors.append("max_entries must be a non-negative integer")
        
        # Check max_age_days
        max_age_days = self.get_rule("max_age_days")
        if max_age_days is not None:
            if not isinstance(max_age_days, int) or max_age_days < 0:
                errors.append("max_age_days must be a non-negative integer")
        
        # Check tag lists
        for tag_field in ["allowed_tags", "excluded_tags"]:
            tag_list = self.get_rule(tag_field)
            if tag_list is not None:
                if not isinstance(tag_list, list):
                    errors.append(f"{tag_field} must be a list")
                elif not all(isinstance(tag, str) for tag in tag_list):
                    errors.append(f"All items in {tag_field} must be strings")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if this permission has valid configuration."""
        return len(self.validate_rules()) == 0
    
    @classmethod
    def create_default_permission(cls, model_id: str, scope: str = "basic") -> "Permission":
        """
        Create a default permission for a model.
        
        Args:
            model_id: The model identifier
            scope: The default scope to grant
            
        Returns:
            New Permission instance with default settings
        """
        return cls(
            model_id=model_id,
            scope=scope,
            description=f"Default permission for {model_id}",
            rules={
                "max_entries": 50,
                "max_age_days": 30,
            }
        )
