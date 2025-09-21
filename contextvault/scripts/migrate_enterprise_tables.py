#!/usr/bin/env python3
"""
Database migration script for enterprise features.
Creates all new tables for multi-user support, audit trails, versioning, and compliance.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from contextvault.database import get_db_context, Base, engine
# User models removed - no multi-user support
from contextvault.models.context_versions import ContextVersion, ChangeType
from contextvault.models.audit import AuditLog, AuditEventType, ComplianceReport
from contextvault.models.models import AIModel, ModelProvider, ModelStatus
from contextvault.models.context_relationships import ContextRelationship, RelationshipType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_enterprise_tables():
    """Create all enterprise tables."""
    try:
        logger.info("Starting enterprise database migration...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All enterprise tables created successfully")
        
        # Verify tables were created
        with get_db_context() as db:
            # Check if tables exist by trying to query them
            tables_to_check = [
                'context_versions', 'audit_logs', 
                'compliance_reports', 'ai_models', 'context_relationships'
            ]
            
            for table in tables_to_check:
                try:
                    from sqlalchemy import text
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"✅ Table '{table}' exists and is accessible ({count} records)")
                except Exception as e:
                    logger.error(f"❌ Table '{table}' failed: {e}")
                    return False
        
        logger.info("🎉 Enterprise database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False


def create_test_data():
    """Create test data for enterprise features."""
    try:
        logger.info("Creating test data...")
        
        with get_db_context() as db:
            # Create test AI model
            test_model = AIModel(
                model_id="test-model-1",
                name="Test Model",
                provider=ModelProvider.OLLAMA,
                status=ModelStatus.ACTIVE,
                capabilities={"coding": 0.8, "creative": 0.6},
                performance_metrics={"avg_response_time": 1.5}
            )
            db.add(test_model)
            db.commit()
            db.refresh(test_model)
            logger.info(f"✅ Created test AI model: {test_model.name}")
            
            # Create test audit log
            test_audit = AuditLog.create_audit_log(
                event_type=AuditEventType.SYSTEM_START,
                user_id="system",
                event_data={"system": "enterprise_migration"},
                ip_address="127.0.0.1",
                user_agent="migration_script"
            )
            db.add(test_audit)
            db.commit()
            db.refresh(test_audit)
            logger.info(f"✅ Created test audit log: {test_audit.id}")
            
            logger.info("✅ Test data created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test data creation failed: {e}")
        return False


def verify_migration():
    """Verify that the migration was successful."""
    try:
        logger.info("Verifying migration...")
        
        with get_db_context() as db:
            # Check AI models table
            model_count = db.query(AIModel).count()
            logger.info(f"✅ AI Models table: {model_count} records")
            
            # Check audit logs table
            audit_count = db.query(AuditLog).count()
            logger.info(f"✅ Audit Logs table: {audit_count} records")
            
            # Check context versions table
            version_count = db.query(ContextVersion).count()
            logger.info(f"✅ Context Versions table: {version_count} records")
            
            # Check context relationships table
            relationship_count = db.query(ContextRelationship).count()
            logger.info(f"✅ Context Relationships table: {relationship_count} records")
            
            logger.info("✅ Migration verification completed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False


def main():
    """Main migration function."""
    print("🚀 Starting Enterprise Database Migration")
    print("=" * 50)
    
    # Step 1: Create tables
    if not create_enterprise_tables():
        print("❌ Table creation failed")
        return False
    
    # Step 2: Create test data
    if not create_test_data():
        print("❌ Test data creation failed")
        return False
    
    # Step 3: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    print("=" * 50)
    print("🎉 ENTERPRISE DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
    print("✅ All enterprise tables created")
    print("✅ Test data created")
    print("✅ Migration verified")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
