#!/usr/bin/env python3
"""Database initialization script for ContextVault."""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path so we can import contextvault
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import init_database, check_database_connection, get_database_info
from contextvault.config import settings, validate_environment
from contextvault.models import Permission


def setup_logging():
    """Setup logging for the initialization script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def create_default_permissions():
    """Create default permission rules for common models."""
    from contextvault.database import get_db_context
    
    default_permissions = [
        {
            "model_id": "llama2",
            "model_name": "Llama 2",
            "scope": "preferences,notes",
            "description": "Default permissions for Llama 2 - access to preferences and notes",
            "rules": {
                "max_entries": 50,
                "max_age_days": 30,
            }
        },
        {
            "model_id": "codellama", 
            "model_name": "Code Llama",
            "scope": "preferences,notes,files",
            "description": "Default permissions for Code Llama - includes file access for coding context",
            "rules": {
                "max_entries": 100,
                "max_age_days": 60,
                "allowed_tags": ["coding", "programming", "development", "work"],
            }
        },
        {
            "model_id": "mistral",
            "model_name": "Mistral",
            "scope": "basic",
            "description": "Basic permissions for Mistral model",
            "rules": {
                "max_entries": 25,
                "max_age_days": 14,
            }
        },
    ]
    
    try:
        with get_db_context() as db:
            created_count = 0
            
            for perm_data in default_permissions:
                # Check if permission already exists
                existing = db.query(Permission).filter(
                    Permission.model_id == perm_data["model_id"]
                ).first()
                
                if not existing:
                    permission = Permission(**perm_data)
                    db.add(permission)
                    created_count += 1
                    print(f"✓ Created default permission for {perm_data['model_id']}")
                else:
                    print(f"- Permission for {perm_data['model_id']} already exists")
            
            if created_count > 0:
                db.commit()
                print(f"\n✓ Created {created_count} default permissions")
            else:
                print("\n- No new default permissions needed")
                
    except Exception as e:
        print(f"✗ Error creating default permissions: {e}")
        return False
    
    return True


def main():
    """Main initialization function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 Initializing ContextVault Database\n")
    
    # Validate environment
    print("1. Validating environment...")
    env_status = validate_environment()
    
    if env_status["issues"]:
        print("✗ Environment validation failed:")
        for issue in env_status["issues"]:
            print(f"   - {issue}")
        return 1
    
    if env_status["warnings"]:
        print("⚠ Environment warnings:")
        for warning in env_status["warnings"]:
            print(f"   - {warning}")
    
    print("✓ Environment validation passed\n")
    
    # Check database connection
    print("2. Testing database connection...")
    if not check_database_connection():
        print("✗ Cannot connect to database")
        print("   Check your DATABASE_URL configuration in .env")
        return 1
    
    db_info = get_database_info()
    print(f"✓ Connected to {db_info['driver']} database")
    print(f"   URL: {db_info['url']}\n")
    
    # Initialize database
    print("3. Creating database tables...")
    try:
        init_database()
        print("✓ Database tables created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        return 1
    
    # Create default permissions
    print("4. Setting up default permissions...")
    if not create_default_permissions():
        print("⚠ Warning: Some default permissions could not be created\n")
    else:
        print()
    
    # Display configuration summary
    print("5. Configuration Summary:")
    print(f"   - Database: {settings.database_url}")
    print(f"   - API Host: {settings.api_host}:{settings.api_port}")
    print(f"   - Ollama Integration: {settings.ollama_host}:{settings.ollama_port}")
    print(f"   - Proxy Port: {settings.proxy_port}")
    print(f"   - Max Context Entries: {settings.max_context_entries}")
    print(f"   - Max Context Length: {settings.max_context_length}")
    print(f"   - Log Level: {settings.log_level}")
    print()
    
    print("🎉 ContextVault database initialization completed successfully!")
    print()
    print("Next steps:")
    print("   1. Start the API server: contextvault serve")
    print("   2. Add some context: contextvault context add 'Your first context entry'")
    print("   3. Set up model permissions: contextvault permissions add your-model --scope=preferences")
    print("   4. Visit http://localhost:8000/docs for API documentation")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
