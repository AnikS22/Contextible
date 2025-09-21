#!/usr/bin/env python3
"""
Enhanced Schema Migration Script
Migrates the database to support intelligent context management
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context, init_database
from contextvault.models.context import ContextEntry, ContextCategory, ContextSource, ValidationStatus, ContextType
from sqlalchemy import text


def migrate_to_enhanced_schema():
    """Migrate database to enhanced schema."""
    print("🔄 Starting Enhanced Schema Migration")
    print("=" * 50)
    
    # Initialize database connection
    init_database()
    
    with get_db_context() as db:
        # Check if migration is needed
        if _is_migration_needed(db):
            print("✅ Migration needed - proceeding...")
            
            # Step 1: Add new columns
            _add_new_columns(db)
            
            # Step 2: Create new tables
            _create_new_tables(db)
            
            # Step 3: Create indexes
            _create_indexes(db)
            
            # Step 4: Migrate existing data
            _migrate_existing_data(db)
            
            # Step 5: Update metadata
            _update_metadata(db)
            
            print("✅ Enhanced schema migration completed successfully!")
            
        else:
            print("ℹ️ Database already has enhanced schema - no migration needed")
    
    print("🎉 Migration process completed!")


def _is_migration_needed(db) -> bool:
    """Check if migration is needed by looking for new columns."""
    try:
        # Try to query a new column
        result = db.execute(text("SELECT context_source FROM context_entries LIMIT 1"))
        return False  # Column exists, no migration needed
    except Exception:
        return True  # Column doesn't exist, migration needed


def _add_new_columns(db):
    """Add new columns to the context_entries table."""
    print("📝 Adding new columns...")
    
    new_columns = [
        ("context_source", "VARCHAR(50) DEFAULT 'manual'"),
        ("confidence_score", "FLOAT DEFAULT 1.0"),
        ("context_category", "VARCHAR(50) DEFAULT 'other'"),
        ("parent_context_id", "VARCHAR(36)"),
        ("validation_status", "VARCHAR(50) DEFAULT 'pending'"),
        ("extraction_metadata", "JSON")
    ]
    
    for column_name, column_definition in new_columns:
        try:
            db.execute(text(f"ALTER TABLE context_entries ADD COLUMN {column_name} {column_definition}"))
            print(f"  ✅ Added column: {column_name}")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print(f"  ℹ️ Column {column_name} already exists")
            else:
                print(f"  ❌ Failed to add column {column_name}: {e}")
    
    db.commit()


def _create_new_tables(db):
    """Create new tables for enhanced functionality."""
    print("📋 Creating new tables...")
    
    # Context relationships table
    relationships_table_sql = """
    CREATE TABLE IF NOT EXISTS context_relationships (
        id VARCHAR(36) PRIMARY KEY,
        source_context_id VARCHAR(36) NOT NULL,
        target_context_id VARCHAR(36) NOT NULL,
        relationship_type VARCHAR(50) NOT NULL,
        confidence FLOAT DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_context_id) REFERENCES context_entries(id),
        FOREIGN KEY (target_context_id) REFERENCES context_entries(id),
        UNIQUE(source_context_id, target_context_id, relationship_type)
    )
    """
    
    try:
        db.execute(text(relationships_table_sql))
        print("  ✅ Created context_relationships table")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ context_relationships table already exists")
        else:
            print(f"  ❌ Failed to create context_relationships table: {e}")
    
    # Context usage stats table
    usage_stats_table_sql = """
    CREATE TABLE IF NOT EXISTS context_usage_stats (
        id VARCHAR(36) PRIMARY KEY,
        context_id VARCHAR(36) NOT NULL,
        usage_type VARCHAR(50) NOT NULL,
        usage_count INTEGER DEFAULT 0,
        last_used_at TIMESTAMP,
        usage_metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (context_id) REFERENCES context_entries(id),
        UNIQUE(context_id, usage_type)
    )
    """
    
    try:
        db.execute(text(usage_stats_table_sql))
        print("  ✅ Created context_usage_stats table")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ context_usage_stats table already exists")
        else:
            print(f"  ❌ Failed to create context_usage_stats table: {e}")
    
    db.commit()


def _create_indexes(db):
    """Create indexes for better performance."""
    print("🔍 Creating indexes...")
    
    indexes = [
        ("idx_context_category", "context_entries", "context_category"),
        ("idx_context_source", "context_entries", "context_source"),
        ("idx_validation_status", "context_entries", "validation_status"),
        ("idx_confidence_score", "context_entries", "confidence_score"),
        ("idx_parent_context", "context_entries", "parent_context_id"),
        ("idx_created_at", "context_entries", "created_at"),
        ("idx_access_count", "context_entries", "access_count"),
        ("idx_relationships_source", "context_relationships", "source_context_id"),
        ("idx_relationships_target", "context_relationships", "target_context_id"),
        ("idx_usage_stats_context", "context_usage_stats", "context_id")
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            db.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})"))
            print(f"  ✅ Created index: {index_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ℹ️ Index {index_name} already exists")
            else:
                print(f"  ❌ Failed to create index {index_name}: {e}")
    
    db.commit()


def _migrate_existing_data(db):
    """Migrate existing data to use new fields."""
    print("📊 Migrating existing data...")
    
    # Get all existing context entries
    existing_contexts = db.query(ContextEntry).all()
    print(f"  Found {len(existing_contexts)} existing context entries")
    
    migrated_count = 0
    
    for context in existing_contexts:
        updated = False
        
        # Set context_source based on existing metadata
        if not hasattr(context, 'context_source') or context.context_source is None:
            if context.entry_metadata and context.entry_metadata.get('auto_extracted'):
                context.context_source = ContextSource.EXTRACTED
            elif context.source and 'conversation' in context.source.lower():
                context.context_source = ContextSource.CONVERSATION
            elif context.source and 'import' in context.source.lower():
                context.context_source = ContextSource.IMPORTED
            else:
                context.context_source = ContextSource.MANUAL
            updated = True
        
        # Set confidence_score
        if not hasattr(context, 'confidence_score') or context.confidence_score is None:
            # Set confidence based on source
            if context.context_source == ContextSource.MANUAL:
                context.confidence_score = 1.0
            elif context.context_source == ContextSource.EXTRACTED:
                context.confidence_score = 0.7
            else:
                context.confidence_score = 0.8
            updated = True
        
        # Set context_category
        if not hasattr(context, 'context_category') or context.context_category is None:
            # Categorize based on content
            from contextvault.services.categorizer import context_categorizer
            categorization = context_categorizer.categorize_context(context.content)
            context.context_category = categorization.context_category
            updated = True
        
        # Set validation_status
        if not hasattr(context, 'validation_status') or context.validation_status is None:
            if context.context_source == ContextSource.MANUAL:
                context.validation_status = ValidationStatus.CONFIRMED
            else:
                context.validation_status = ValidationStatus.PENDING
            updated = True
        
        # Set extraction_metadata
        if not hasattr(context, 'extraction_metadata') or context.extraction_metadata is None:
            context.extraction_metadata = {
                "migrated_from_legacy": True,
                "migration_timestamp": datetime.utcnow().isoformat()
            }
            updated = True
        
        if updated:
            migrated_count += 1
    
    db.commit()
    print(f"  ✅ Migrated {migrated_count} context entries")


def _update_metadata(db):
    """Update database metadata."""
    print("📝 Updating database metadata...")
    
    # Create migration record
    migration_metadata = {
        "migration_version": "enhanced_schema_v1",
        "migration_timestamp": datetime.utcnow().isoformat(),
        "features_added": [
            "context_source",
            "confidence_score", 
            "context_category",
            "parent_context_id",
            "validation_status",
            "extraction_metadata",
            "context_relationships",
            "context_usage_stats"
        ]
    }
    
    # Store in a simple metadata table
    metadata_table_sql = """
    CREATE TABLE IF NOT EXISTS migration_metadata (
        id VARCHAR(36) PRIMARY KEY,
        migration_version VARCHAR(100) NOT NULL,
        migration_data JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        db.execute(text(metadata_table_sql))
        db.execute(text(
            "INSERT INTO migration_metadata (id, migration_version, migration_data) VALUES (:id, :version, :data)"
        ), {
            "id": str(uuid.uuid4()),
            "version": migration_metadata["migration_version"],
            "data": json.dumps(migration_metadata)
        })
        print("  ✅ Created migration metadata record")
    except Exception as e:
        print(f"  ⚠️ Failed to create migration metadata: {e}")
    
    db.commit()


def verify_migration():
    """Verify that the migration was successful."""
    print("\n🔍 Verifying migration...")
    
    with get_db_context() as db:
        # Check new columns exist
        new_columns = ["context_source", "confidence_score", "context_category", "validation_status"]
        for column in new_columns:
            try:
                result = db.execute(text(f"SELECT {column} FROM context_entries LIMIT 1"))
                print(f"  ✅ Column {column} exists")
            except Exception as e:
                print(f"  ❌ Column {column} missing: {e}")
        
        # Check new tables exist
        new_tables = ["context_relationships", "context_usage_stats"]
        for table in new_tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                print(f"  ✅ Table {table} exists")
            except Exception as e:
                print(f"  ❌ Table {table} missing: {e}")
        
        # Check data migration
        total_contexts = db.query(ContextEntry).count()
        contexts_with_source = db.query(ContextEntry).filter(
            ContextEntry.context_source.isnot(None)
        ).count()
        
        print(f"  📊 Total contexts: {total_contexts}")
        print(f"  📊 Contexts with context_source: {contexts_with_source}")
        
        if contexts_with_source == total_contexts:
            print("  ✅ All contexts have context_source")
        else:
            print(f"  ⚠️ {total_contexts - contexts_with_source} contexts missing context_source")


def main():
    """Main migration function."""
    print("🚀 ContextVault Enhanced Schema Migration")
    print("=" * 60)
    
    try:
        # Run migration
        migrate_to_enhanced_schema()
        
        # Verify migration
        verify_migration()
        
        print("\n🎉 Migration completed successfully!")
        print("ContextVault now supports intelligent context management!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import json
    import uuid
    from datetime import datetime
    sys.exit(main())
