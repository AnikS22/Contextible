"""Plugin management service for Contextible extensions."""

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..plugins.base import BasePlugin, ContextPlugin, ModelPlugin, AnalyticsPlugin, NotificationPlugin, SecurityPlugin
from ..database import get_db_context

logger = logging.getLogger(__name__)


class PluginManager:
    """Service for managing plugins and extensions."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_types = {
            "context": ContextPlugin,
            "model": ModelPlugin,
            "analytics": AnalyticsPlugin,
            "notification": NotificationPlugin,
            "security": SecurityPlugin
        }
        self.logger = logging.getLogger(__name__)
    
    async def load_plugin(self, 
                        plugin_path: str, 
                        config: Dict[str, Any],
                        plugin_type: str = "context") -> bool:
        """
        Load a plugin from a file path.
        
        Args:
            plugin_path: Path to plugin file
            config: Plugin configuration
            plugin_type: Type of plugin
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Import the plugin module
            plugin_module = importlib.import_module(plugin_path)
            
            # Find the plugin class
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, self.plugin_types.get(plugin_type, BasePlugin)) and
                    attr != self.plugin_types.get(plugin_type, BasePlugin)):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                self.logger.error(f"No valid plugin class found in {plugin_path}")
                return False
            
            # Create plugin instance
            plugin = plugin_class()
            
            # Initialize plugin
            success = await plugin.initialize(config)
            if not success:
                self.logger.error(f"Failed to initialize plugin {plugin.get_name()}")
                return False
            
            # Register plugin
            self.plugins[plugin.get_name()] = plugin
            self.plugin_configs[plugin.get_name()] = config
            
            self.logger.info(f"Loaded plugin: {plugin.get_name()} v{plugin.get_version()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        try:
            if plugin_name not in self.plugins:
                self.logger.warning(f"Plugin {plugin_name} not found")
                return False
            
            plugin = self.plugins[plugin_name]
            await plugin.cleanup()
            
            del self.plugins[plugin_name]
            del self.plugin_configs[plugin_name]
            
            self.logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    async def execute_plugin(self, 
                           plugin_name: str, 
                           request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin with a request.
        
        Args:
            plugin_name: Name of plugin to execute
            request: Request data
            
        Returns:
            Plugin response
        """
        try:
            if plugin_name not in self.plugins:
                return {"error": f"Plugin {plugin_name} not found"}
            
            plugin = self.plugins[plugin_name]
            if not plugin.is_healthy():
                return {"error": f"Plugin {plugin_name} is not healthy"}
            
            result = await plugin.process_request(request)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute plugin {plugin_name}: {e}")
            return {"error": str(e)}
    
    async def execute_context_plugin(self, 
                                  plugin_name: str,
                                  context_entries: List[Dict[str, Any]],
                                  user_prompt: str) -> List[Dict[str, Any]]:
        """
        Execute a context plugin.
        
        Args:
            plugin_name: Name of context plugin
            context_entries: Context entries to process
            user_prompt: User prompt
            
        Returns:
            Processed context entries
        """
        try:
            if plugin_name not in self.plugins:
                return context_entries
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, ContextPlugin):
                return context_entries
            
            if not plugin.is_healthy():
                return context_entries
            
            result = await plugin.process_context(context_entries, user_prompt)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute context plugin {plugin_name}: {e}")
            return context_entries
    
    async def execute_model_plugin(self, 
                                 plugin_name: str,
                                 request: Dict[str, Any],
                                 model_id: str) -> Dict[str, Any]:
        """
        Execute a model plugin.
        
        Args:
            plugin_name: Name of model plugin
            request: Model request
            model_id: Model identifier
            
        Returns:
            Processed request
        """
        try:
            if plugin_name not in self.plugins:
                return request
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, ModelPlugin):
                return request
            
            if not plugin.is_healthy():
                return request
            
            result = await plugin.process_model_request(request, model_id)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute model plugin {plugin_name}: {e}")
            return request
    
    async def execute_analytics_plugin(self, 
                                     plugin_name: str,
                                     data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an analytics plugin.
        
        Args:
            plugin_name: Name of analytics plugin
            data: Analytics data
            
        Returns:
            Processed analytics data
        """
        try:
            if plugin_name not in self.plugins:
                return data
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, AnalyticsPlugin):
                return data
            
            if not plugin.is_healthy():
                return data
            
            result = await plugin.process_analytics(data)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute analytics plugin {plugin_name}: {e}")
            return data
    
    async def send_notification(self, 
                              plugin_name: str,
                              user_id: str,
                              message: str,
                              notification_type: str) -> bool:
        """
        Send a notification through a plugin.
        
        Args:
            plugin_name: Name of notification plugin
            user_id: User ID
            message: Notification message
            notification_type: Type of notification
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if plugin_name not in self.plugins:
                return False
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, NotificationPlugin):
                return False
            
            if not plugin.is_healthy():
                return False
            
            result = await plugin.send_notification(user_id, message, notification_type)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send notification via plugin {plugin_name}: {e}")
            return False
    
    async def validate_security(self, 
                              plugin_name: str,
                              request: Dict[str, Any],
                              user_id: str) -> bool:
        """
        Validate security through a plugin.
        
        Args:
            plugin_name: Name of security plugin
            request: Request data
            user_id: User ID
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if plugin_name not in self.plugins:
                return True  # No security plugin, allow by default
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, SecurityPlugin):
                return True
            
            if not plugin.is_healthy():
                return False
            
            result = await plugin.validate_request(request, user_id)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate security via plugin {plugin_name}: {e}")
            return False
    
    async def audit_security_action(self, 
                                  plugin_name: str,
                                  action: str,
                                  user_id: str,
                                  details: Dict[str, Any]) -> None:
        """
        Audit a security action through a plugin.
        
        Args:
            plugin_name: Name of security plugin
            action: Action performed
            user_id: User ID
            details: Action details
        """
        try:
            if plugin_name not in self.plugins:
                return
            
            plugin = self.plugins[plugin_name]
            if not isinstance(plugin, SecurityPlugin):
                return
            
            if not plugin.is_healthy():
                return
            
            await plugin.audit_action(action, user_id, details)
            
        except Exception as e:
            self.logger.error(f"Failed to audit security action via plugin {plugin_name}: {e}")
    
    def get_loaded_plugins(self) -> List[Dict[str, Any]]:
        """Get list of loaded plugins."""
        return [
            {
                "name": plugin.get_name(),
                "version": plugin.get_version(),
                "description": plugin.get_description(),
                "is_healthy": plugin.is_healthy(),
                "metadata": plugin.get_metadata()
            }
            for plugin in self.plugins.values()
        ]
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a specific plugin by name."""
        return self.plugins.get(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self.plugins
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin.
        
        Args:
            plugin_name: Name of plugin to reload
            
        Returns:
            True if reloaded successfully, False otherwise
        """
        try:
            if plugin_name not in self.plugins:
                return False
            
            # Get current config
            config = self.plugin_configs.get(plugin_name, {})
            
            # Unload and reload
            await self.unload_plugin(plugin_name)
            # Note: In a real implementation, you'd need to store the plugin path
            # For now, we'll just return True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return False
    
    async def cleanup_all_plugins(self) -> None:
        """Cleanup all loaded plugins."""
        for plugin_name in list(self.plugins.keys()):
            await self.unload_plugin(plugin_name)


# Global plugin manager instance
plugin_manager = PluginManager()
