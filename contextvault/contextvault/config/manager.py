"""
Configuration Manager for ContextVault
Handles user preferences and configuration persistence
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class UserPreferences:
    """User preference settings."""
    theme: str = "dark"  # dark, light
    auto_start_services: bool = True
    notifications: bool = True
    default_template: str = "forced_reference"
    max_context_length: int = 1000
    auto_extract_context: bool = True
    show_debug_info: bool = False


@dataclass
class SystemConfig:
    """System configuration settings."""
    setup_completed: bool = False
    setup_date: float = 0.0
    version: str = "0.1.0"
    api_host: str = "localhost"
    api_port: int = 8000
    proxy_port: int = 11435
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    database_path: str = "./contextvault.db"


class ConfigManager:
    """Manages ContextVault configuration and user preferences."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".contextvault"
        
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.preferences_file = self.config_dir / "preferences.json"
        
        # Load configuration
        self.system_config = self._load_system_config()
        self.user_preferences = self._load_user_preferences()
    
    def _load_system_config(self) -> SystemConfig:
        """Load system configuration from file."""
        if not self.config_file.exists():
            return SystemConfig()
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Convert dict to SystemConfig
            return SystemConfig(**{k: v for k, v in data.items() if hasattr(SystemConfig, k)})
        except Exception:
            return SystemConfig()
    
    def _load_user_preferences(self) -> UserPreferences:
        """Load user preferences from file."""
        if not self.preferences_file.exists():
            return UserPreferences()
        
        try:
            with open(self.preferences_file, 'r') as f:
                data = json.load(f)
            
            # Convert dict to UserPreferences
            return UserPreferences(**{k: v for k, v in data.items() if hasattr(UserPreferences, k)})
        except Exception:
            return UserPreferences()
    
    def save_system_config(self) -> bool:
        """Save system configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.system_config), f, indent=2)
            return True
        except Exception:
            return False
    
    def save_user_preferences(self) -> bool:
        """Save user preferences to file."""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(asdict(self.user_preferences), f, indent=2)
            return True
        except Exception:
            return False
    
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self.system_config.setup_completed
    
    def mark_setup_completed(self) -> bool:
        """Mark setup as completed."""
        self.system_config.setup_completed = True
        self.system_config.setup_date = time.time()
        return self.save_system_config()
    
    def get_setup_info(self) -> Dict[str, Any]:
        """Get setup information."""
        return {
            "setup_completed": self.system_config.setup_completed,
            "setup_date": time.ctime(self.system_config.setup_date) if self.system_config.setup_date else None,
            "version": self.system_config.version,
            "config_dir": str(self.config_dir),
            "config_file": str(self.config_file),
            "preferences_file": str(self.preferences_file)
        }
    
    def update_system_config(self, **kwargs) -> bool:
        """Update system configuration."""
        for key, value in kwargs.items():
            if hasattr(self.system_config, key):
                setattr(self.system_config, key, value)
        
        return self.save_system_config()
    
    def update_user_preferences(self, **kwargs) -> bool:
        """Update user preferences."""
        for key, value in kwargs.items():
            if hasattr(self.user_preferences, key):
                setattr(self.user_preferences, key, value)
        
        return self.save_user_preferences()
    
    def reset_config(self) -> bool:
        """Reset all configuration to defaults."""
        try:
            # Remove config files
            if self.config_file.exists():
                self.config_file.unlink()
            if self.preferences_file.exists():
                self.preferences_file.unlink()
            
            # Reset to defaults
            self.system_config = SystemConfig()
            self.user_preferences = UserPreferences()
            
            return True
        except Exception:
            return False
    
    def export_config(self, file_path: Path) -> bool:
        """Export configuration to a file."""
        try:
            export_data = {
                "system_config": asdict(self.system_config),
                "user_preferences": asdict(self.user_preferences),
                "export_date": time.time(),
                "export_version": self.system_config.version
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_config(self, file_path: Path) -> bool:
        """Import configuration from a file."""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Import system config
            if "system_config" in import_data:
                for key, value in import_data["system_config"].items():
                    if hasattr(self.system_config, key):
                        setattr(self.system_config, key, value)
            
            # Import user preferences
            if "user_preferences" in import_data:
                for key, value in import_data["user_preferences"].items():
                    if hasattr(self.user_preferences, key):
                        setattr(self.user_preferences, key, value)
            
            # Save imported configuration
            return self.save_system_config() and self.save_user_preferences()
            
        except Exception:
            return False
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get theme colors based on user preference."""
        if self.user_preferences.theme == "light":
            return {
                "primary": "#A892F5",
                "background": "#FFFFFF",
                "surface": "#FAFAFA",
                "text": "#000000",
                "text_secondary": "#555555",
                "success": "#48BB78",
                "warning": "#ED8936",
                "error": "#F56565"
            }
        else:  # dark theme
            return {
                "primary": "#A892F5",
                "background": "#1A1A1A",
                "surface": "#2D2D2D",
                "text": "#FFFFFF",
                "text_secondary": "#CCCCCC",
                "success": "#48BB78",
                "warning": "#ED8936",
                "error": "#F56565"
            }
    
    def get_available_themes(self) -> Dict[str, Dict[str, str]]:
        """Get available themes."""
        return {
            "dark": {
                "name": "Dark Theme",
                "description": "Dark background with light text",
                "colors": self.get_theme_colors()
            },
            "light": {
                "name": "Light Theme", 
                "description": "Light background with dark text",
                "colors": self.get_theme_colors()
            }
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        issues = []
        warnings = []
        
        # Check system config
        if not self.system_config.setup_completed:
            warnings.append("Setup not completed")
        
        if self.system_config.api_port == self.system_config.proxy_port:
            issues.append("API port and proxy port cannot be the same")
        
        if self.system_config.ollama_port == self.system_config.proxy_port:
            issues.append("Ollama port and proxy port cannot be the same")
        
        # Check user preferences
        if self.user_preferences.max_context_length < 100:
            warnings.append("Max context length is very low")
        
        if self.user_preferences.max_context_length > 10000:
            warnings.append("Max context length is very high")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# Global config manager instance
config_manager = ConfigManager()
