#!/usr/bin/env python3
"""
Simple CLI entry point for ContextVault.
This is a working CLI that actually functions.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Main CLI entry point."""
    print("🧠 Contextible CLI")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  init     - Initialize database")
        print("  status   - Show system status")
        print("  context  - Manage context entries")
        print("  models   - Manage AI models")
        print("  audit    - View audit logs")
        print("  help     - Show this help")
        return 0
    
    command = sys.argv[1]
    
    if command == "init":
        return init_database()
    elif command == "status":
        return show_status()
    elif command == "context":
        return manage_context()
    elif command == "models":
        return manage_models()
    elif command == "audit":
        return view_audit()
    elif command == "help":
        return show_help()
    else:
        print(f"Unknown command: {command}")
        return 1

def init_database():
    """Initialize the database."""
    print("🚀 Initializing database...")
    try:
        from contextvault.database import get_db_context, Base, engine
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
        return 0
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1

def show_status():
    """Show system status."""
    print("📊 System Status")
    print("=" * 30)
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models.context import ContextEntry
        from contextvault.models.audit import AuditLog
        
        with get_db_context() as db:
            context_count = db.query(ContextEntry).count()
            audit_count = db.query(AuditLog).count()
            
            print(f"Context entries: {context_count}")
            print(f"Audit logs: {audit_count}")
            print("✅ Database connection: OK")
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return 1
    
    return 0

def manage_context():
    """Manage context entries."""
    print("📝 Context Management")
    print("=" * 30)
    
    if len(sys.argv) < 3:
        print("Usage: context <add|list|delete>")
        return 1
    
    action = sys.argv[2]
    
    if action == "add":
        if len(sys.argv) < 4:
            print("Usage: context add <content>")
            return 1
        
        content = " ".join(sys.argv[3:])
        return add_context(content)
    elif action == "list":
        return list_context()
    elif action == "delete":
        if len(sys.argv) < 4:
            print("Usage: context delete <id>")
            return 1
        
        context_id = sys.argv[3]
        return delete_context(context_id)
    else:
        print(f"Unknown action: {action}")
        return 1

def add_context(content):
    """Add a context entry."""
    try:
        from contextvault.database import get_db_context
        from contextvault.models.context import ContextEntry, ContextType, ContextCategory
        
        with get_db_context() as db:
            new_context = ContextEntry(
                content=content,
                context_type=ContextType.TEXT,
                context_category=ContextCategory.OTHER,
                user_id="cli_user"
            )
            db.add(new_context)
            db.commit()
            print(f"✅ Context added: {new_context.id}")
            return 0
    except Exception as e:
        print(f"❌ Failed to add context: {e}")
        return 1

def list_context():
    """List context entries."""
    try:
        from contextvault.database import get_db_context
        from contextvault.models.context import ContextEntry
        
        with get_db_context() as db:
            contexts = db.query(ContextEntry).all()
            
            if not contexts:
                print("No context entries found")
                return 0
            
            print(f"Found {len(contexts)} context entries:")
            for ctx in contexts:
                print(f"  {ctx.id}: {ctx.content[:50]}...")
            
            return 0
    except Exception as e:
        print(f"❌ Failed to list context: {e}")
        return 1

def delete_context(context_id):
    """Delete a context entry."""
    try:
        from contextvault.database import get_db_context
        from contextvault.models.context import ContextEntry
        
        with get_db_context() as db:
            context = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not context:
                print(f"❌ Context not found: {context_id}")
                return 1
            
            db.delete(context)
            db.commit()
            print(f"✅ Context deleted: {context_id}")
            return 0
    except Exception as e:
        print(f"❌ Failed to delete context: {e}")
        return 1

def manage_models():
    """Manage AI models."""
    print("🤖 AI Model Management")
    print("=" * 30)
    
    try:
        from contextvault.services.model_manager import model_manager
        import asyncio
        
        async def get_models():
            return await model_manager.get_available_models()
        
        models = asyncio.run(get_models())
        
        if not models:
            print("No AI models available")
            print("To add models, configure your AI provider (Ollama, LM Studio, etc.)")
        else:
            print(f"Found {len(models)} models:")
            for model in models:
                print(f"  {model.get('name', 'Unknown')}: {model.get('provider', 'Unknown')}")
        
        return 0
    except Exception as e:
        print(f"❌ Failed to manage models: {e}")
        return 1

def view_audit():
    """View audit logs."""
    print("📋 Audit Logs")
    print("=" * 30)
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models.audit import AuditLog
        
        with get_db_context() as db:
            logs = db.query(AuditLog).order_by(AuditLog.event_timestamp.desc()).limit(10).all()
            
            if not logs:
                print("No audit logs found")
                return 0
            
            print(f"Recent audit logs ({len(logs)}):")
            for log in logs:
                print(f"  {log.event_timestamp}: {log.event_type} - {log.user_id}")
            
            return 0
    except Exception as e:
        print(f"❌ Failed to view audit logs: {e}")
        return 1

def show_help():
    """Show help information."""
    print("🧠 Contextible CLI Help")
    print("=" * 50)
    print("Commands:")
    print("  init                    - Initialize database")
    print("  status                  - Show system status")
    print("  context add <content>   - Add context entry")
    print("  context list            - List context entries")
    print("  context delete <id>     - Delete context entry")
    print("  models                  - Show available AI models")
    print("  audit                   - View audit logs")
    print("  help                    - Show this help")
    return 0

if __name__ == "__main__":
    sys.exit(main())
