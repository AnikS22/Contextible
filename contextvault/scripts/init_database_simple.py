#!/usr/bin/env python3
"""
Simple database initialization script for Contextible.
Creates all required tables without complex dependencies.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from contextvault.database import get_db_context, Base, engine
from contextvault.models.context import ContextEntry, ContextType, ContextCategory
from contextvault.models.models import AIModel, ModelProvider, ModelStatus
from contextvault.models.context_relationships import ContextRelationship, RelationshipType
from contextvault.models.context_versions import ContextVersion, ChangeType
from contextvault.models.audit import AuditLog, AuditEventType, ComplianceReport

def init_database():
    """Initialize the database with all required tables."""
    try:
        print("🚀 Initializing Contextible Database...")
        print("=" * 50)
        
        # Create all tables
        print("📁 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # Test database connection
        print("🔍 Testing database connection...")
        with get_db_context() as db:
            # Test context entries table
            context_count = db.query(ContextEntry).count()
            print(f"✅ Context entries table: {context_count} records")
            
            # Test AI models table
            model_count = db.query(AIModel).count()
            print(f"✅ AI models table: {model_count} records")
            
            # Test audit logs table
            audit_count = db.query(AuditLog).count()
            print(f"✅ Audit logs table: {audit_count} records")
            
            # Test context versions table
            version_count = db.query(ContextVersion).count()
            print(f"✅ Context versions table: {version_count} records")
            
            # Test context relationships table
            relationship_count = db.query(ContextRelationship).count()
            print(f"✅ Context relationships table: {relationship_count} records")
        
        print("=" * 50)
        print("🎉 Database initialization completed successfully!")
        print("✅ All tables created and accessible")
        print("✅ Ready to store context entries")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
