"""Base plugin interface for Contextible extensions."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all Contextible plugins."""
    
    def __init__(self, name: str, version: str, description: str = ""):
        """
        Initialize the plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
            description: Plugin description
        """
        self.name = name
        self.version = version
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.is_initialized = False
        self.config = {}
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request through the plugin.
        
        Args:
            request: Request data
            
        Returns:
            Processed request data
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def get_name(self) -> str:
        """Get plugin name."""
        return self.name
    
    def get_version(self) -> str:
        """Get plugin version."""
        return self.version
    
    def get_description(self) -> str:
        """Get plugin description."""
        return self.description
    
    def is_healthy(self) -> bool:
        """Check if plugin is healthy."""
        return self.is_initialized
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "is_initialized": self.is_initialized,
            "config": self.config
        }


class ContextPlugin(BasePlugin):
    """Base class for context-related plugins."""
    
    @abstractmethod
    async def process_context(self, 
                            context_entries: List[Dict[str, Any]],
                            user_prompt: str) -> List[Dict[str, Any]]:
        """
        Process context entries.
        
        Args:
            context_entries: List of context entries
            user_prompt: User prompt
            
        Returns:
            Processed context entries
        """
        pass


class ModelPlugin(BasePlugin):
    """Base class for model-related plugins."""
    
    @abstractmethod
    async def process_model_request(self, 
                                  request: Dict[str, Any],
                                  model_id: str) -> Dict[str, Any]:
        """
        Process a model request.
        
        Args:
            request: Model request data
            model_id: Model identifier
            
        Returns:
            Processed request data
        """
        pass


class AnalyticsPlugin(BasePlugin):
    """Base class for analytics plugins."""
    
    @abstractmethod
    async def process_analytics(self, 
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analytics data.
        
        Args:
            data: Analytics data
            
        Returns:
            Processed analytics data
        """
        pass


class NotificationPlugin(BasePlugin):
    """Base class for notification plugins."""
    
    @abstractmethod
    async def send_notification(self, 
                              user_id: str,
                              message: str,
                              notification_type: str) -> bool:
        """
        Send a notification.
        
        Args:
            user_id: User ID
            message: Notification message
            notification_type: Type of notification
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


class SecurityPlugin(BasePlugin):
    """Base class for security plugins."""
    
    @abstractmethod
    async def validate_request(self, 
                             request: Dict[str, Any],
                             user_id: str) -> bool:
        """
        Validate a request for security.
        
        Args:
            request: Request data
            user_id: User ID
            
        Returns:
            True if request is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def audit_action(self, 
                         action: str,
                         user_id: str,
                         details: Dict[str, Any]) -> None:
        """
        Audit a security action.
        
        Args:
            action: Action performed
            user_id: User ID
            details: Action details
        """
        pass
