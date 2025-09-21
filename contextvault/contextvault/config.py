"""Configuration management for ContextVault."""

import os
from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./contextvault.db", env="DATABASE_URL")
    
    # API Configuration
    api_host: str = Field(default="127.0.0.1", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Ollama Integration
    ollama_host: str = Field(default="127.0.0.1", env="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, env="OLLAMA_PORT")
    proxy_port: int = Field(default=11435, env="PROXY_PORT")
    
    # Context Management
    max_context_entries: int = Field(default=100, env="MAX_CONTEXT_ENTRIES")
    max_context_length: int = Field(default=10000, env="MAX_CONTEXT_LENGTH")
    default_context_retention_days: int = Field(default=90, env="DEFAULT_CONTEXT_RETENTION_DAYS")
    
    # Permission Defaults
    default_model_permissions: str = Field(default="basic", env="DEFAULT_MODEL_PERMISSIONS")
    allow_unknown_models: bool = Field(default=True, env="ALLOW_UNKNOWN_MODELS")
    
    # Performance
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL, handling SQLite path resolution."""
    url = settings.database_url
    if url.startswith("sqlite:"):
        # Ensure SQLite paths are relative to the project root
        if ":///" in url and not os.path.isabs(url.split("///")[1]):
            db_path = url.split("///")[1]
            project_root = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(project_root, db_path)
            url = f"sqlite:///{full_path}"
    return url


def get_context_template() -> str:
    """Get the default context injection template."""
    return """Previous Context:
{context_entries}

Current Conversation:
{user_prompt}"""


def get_allowed_context_types() -> List[str]:
    """Get the list of allowed context types."""
    return ["text", "file", "event", "preference", "note"]


def get_default_permission_scopes() -> List[str]:
    """Get the default permission scopes."""
    return ["basic", "preferences", "notes", "files", "events", "all"]


def validate_environment() -> Dict[str, Any]:
    """Validate the current environment and return a status report."""
    issues = []
    warnings = []
    
    # Check database accessibility
    db_url = get_database_url()
    if db_url.startswith("sqlite:"):
        db_path = db_url.split("///")[1]
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except PermissionError:
                issues.append(f"Cannot create database directory: {db_dir}")
    
    # Check security settings
    if settings.secret_key == "change-me-in-production":
        warnings.append("Using default secret key - change in production")
    
    if not settings.encryption_key:
        warnings.append("No encryption key set - sensitive data will be stored in plaintext")
    
    # Check Ollama connectivity (non-blocking)
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((settings.ollama_host, settings.ollama_port))
        sock.close()
        if result != 0:
            warnings.append(f"Ollama not accessible at {settings.ollama_host}:{settings.ollama_port}")
    except Exception:
        warnings.append("Could not check Ollama connectivity")
    
    return {
        "status": "healthy" if not issues else "error",
        "issues": issues,
        "warnings": warnings,
        "config": {
            "database_url": db_url,
            "api_endpoint": f"http://{settings.api_host}:{settings.api_port}",
            "ollama_endpoint": f"http://{settings.ollama_host}:{settings.ollama_port}",
            "proxy_endpoint": f"http://{settings.api_host}:{settings.proxy_port}",
        }
    }
