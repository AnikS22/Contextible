"""Tests for ContextVault service layer."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contextvault.database import Base
from contextvault.models import ContextEntry, ContextType
from contextvault.services import vault_service, permission_service


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_vault.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = TestingSessionLocal()
    yield session
    session.close()


class TestVaultService:
    """Test VaultService functionality."""
    
    def test_save_context(self, setup_database):
        """Test saving context entries."""
        # Test basic save
        entry = vault_service.save_context(
            content="Test content",
            context_type=ContextType.TEXT,
            source="test",
            tags=["test", "sample"],
            metadata={"test": True}
        )
        
        assert entry.id is not None
        assert entry.content == "Test content"
        assert entry.context_type == ContextType.TEXT
        assert entry.source == "test"
        assert entry.tags == ["test", "sample"]
        assert entry.metadata == {"test": True}
        assert entry.created_at is not None
    
    def test_save_context_validation(self, setup_database):
        """Test validation when saving context."""
        # Test empty content
        with pytest.raises(ValueError, match="Content cannot be empty"):
            vault_service.save_context(content="")
        
        with pytest.raises(ValueError, match="Content cannot be empty"):
            vault_service.save_context(content="   ")
        
        # Test content too long
        long_content = "x" * 100000  # Assuming max is 50000
        with pytest.raises(ValueError, match="Content exceeds maximum length"):
            vault_service.save_context(content=long_content)
    
    def test_get_context(self, setup_database):
        """Test retrieving context entries."""
        # Create test entries
        entry1 = vault_service.save_context(
            content="First entry",
            context_type=ContextType.TEXT,
            tags=["tag1"]
        )
        entry2 = vault_service.save_context(
            content="Second entry",
            context_type=ContextType.PREFERENCE,
            tags=["tag2"]
        )
        
        # Test get all
        entries, total = vault_service.get_context()
        assert len(entries) >= 2
        assert total >= 2
        
        # Test filtering by type
        entries, total = vault_service.get_context(
            filters={"context_types": [ContextType.TEXT]}
        )
        text_entries = [e for e in entries if e.context_type == ContextType.TEXT]
        assert len(text_entries) >= 1
        
        # Test filtering by tags
        entries, total = vault_service.get_context(
            filters={"tags": ["tag1"]}
        )
        tag1_entries = [e for e in entries if e.tags and "tag1" in e.tags]
        assert len(tag1_entries) >= 1
    
    def test_update_context(self, setup_database):
        """Test updating context entries."""
        # Create an entry
        entry = vault_service.save_context(
            content="Original content",
            context_type=ContextType.TEXT,
            tags=["original"]
        )
        
        # Update it
        updated_entry = vault_service.update_context(
            entry.id,
            {
                "content": "Updated content",
                "tags": ["updated"],
                "context_type": ContextType.NOTE
            }
        )
        
        assert updated_entry is not None
        assert updated_entry.content == "Updated content"
        assert updated_entry.tags == ["updated"]
        assert updated_entry.context_type == ContextType.NOTE
        assert updated_entry.updated_at > updated_entry.created_at
    
    def test_update_nonexistent_context(self, setup_database):
        """Test updating non-existent context entry."""
        result = vault_service.update_context(
            "nonexistent-id",
            {"content": "New content"}
        )
        assert result is None
    
    def test_delete_context(self, setup_database):
        """Test deleting context entries."""
        # Create an entry
        entry = vault_service.save_context(
            content="To be deleted",
            context_type=ContextType.TEXT
        )
        
        # Delete it
        success = vault_service.delete_context(entry.id)
        assert success is True
        
        # Verify it's gone
        entries, _ = vault_service.get_context()
        deleted_entries = [e for e in entries if e.id == entry.id]
        assert len(deleted_entries) == 0
    
    def test_delete_nonexistent_context(self, setup_database):
        """Test deleting non-existent context entry."""
        success = vault_service.delete_context("nonexistent-id")
        assert success is False
    
    def test_search_context(self, setup_database):
        """Test searching context entries."""
        # Create test entries
        vault_service.save_context(
            content="Python is a great programming language",
            context_type=ContextType.TEXT,
            tags=["programming"]
        )
        vault_service.save_context(
            content="I love JavaScript for web development",
            context_type=ContextType.TEXT,
            tags=["programming"]
        )
        vault_service.save_context(
            content="My favorite food is pizza",
            context_type=ContextType.PREFERENCE,
            tags=["food"]
        )
        
        # Search for programming content
        entries, total = vault_service.search_context("programming")
        assert len(entries) >= 2
        
        # Search for specific language
        entries, total = vault_service.search_context("Python")
        assert len(entries) >= 1
        python_entries = [e for e in entries if "Python" in e.content]
        assert len(python_entries) >= 1
        
        # Search with no results
        entries, total = vault_service.search_context("nonexistent")
        assert len(entries) == 0
        assert total == 0
    
    def test_get_context_stats(self, setup_database):
        """Test getting context statistics."""
        # Create test entries
        vault_service.save_context(
            content="Text entry",
            context_type=ContextType.TEXT,
            tags=["test"]
        )
        vault_service.save_context(
            content="Preference entry",
            context_type=ContextType.PREFERENCE,
            tags=["test"]
        )
        
        stats = vault_service.get_context_stats()
        
        assert "total_entries" in stats
        assert "entries_by_type" in stats
        assert "most_accessed" in stats
        assert "total_content_length" in stats
        assert "date_range" in stats
        
        assert stats["total_entries"] >= 2
        assert "ContextType.TEXT" in stats["entries_by_type"] or "text" in stats["entries_by_type"]
    
    def test_cleanup_old_entries(self, setup_database):
        """Test cleaning up old entries."""
        # Create an old entry (simulate by creating and then updating its timestamp)
        from contextvault.database import get_db_context
        from datetime import datetime, timedelta
        
        with get_db_context() as db:
            old_entry = ContextEntry(
                content="Old entry",
                context_type=ContextType.TEXT,
                created_at=datetime.utcnow() - timedelta(days=100)
            )
            db.add(old_entry)
            db.commit()
            db.refresh(old_entry)
            
            # Create a recent entry
            recent_entry = vault_service.save_context(
                content="Recent entry",
                context_type=ContextType.TEXT
            )
            
            # Cleanup old entries (older than 90 days)
            deleted_count = vault_service.cleanup_old_entries(retention_days=90)
            assert deleted_count >= 1
            
            # Verify the old entry is gone but recent entry remains
            entries, _ = vault_service.get_context()
            entry_ids = [e.id for e in entries]
            assert old_entry.id not in entry_ids
            assert recent_entry.id in entry_ids
    
    def test_export_context(self, setup_database):
        """Test exporting context data."""
        # Create test entries
        vault_service.save_context(
            content="Export test 1",
            context_type=ContextType.TEXT,
            tags=["export"]
        )
        vault_service.save_context(
            content="Export test 2",
            context_type=ContextType.PREFERENCE,
            tags=["export"]
        )
        
        # Export all data
        export_data = vault_service.export_context()
        
        assert "metadata" in export_data
        assert "entries" in export_data
        assert export_data["metadata"]["total_entries"] >= 2
        assert len(export_data["entries"]) >= 2
        
        # Test export with filters
        export_data = vault_service.export_context(
            filters={"context_types": [ContextType.TEXT]}
        )
        
        # All exported entries should be TEXT type
        for entry_data in export_data["entries"]:
            assert entry_data["context_type"] == "text"


class TestPermissionService:
    """Test PermissionService functionality."""
    
    def test_create_permission_rule(self, setup_database):
        """Test creating permission rules."""
        permission = permission_service.create_permission_rule(
            model_id="test_model",
            scopes=["preferences", "notes"],
            rules={"max_entries": 50},
            description="Test permission"
        )
        
        assert permission.model_id == "test_model"
        assert permission.scope == "preferences,notes"
        assert permission.rules == {"max_entries": 50}
        assert permission.description == "Test permission"
        assert permission.is_active is True
    
    def test_get_allowed_scopes(self, setup_database):
        """Test getting allowed scopes for a model."""
        # Create permission
        permission_service.create_permission_rule(
            model_id="scoped_model",
            scopes=["preferences", "notes"]
        )
        
        scopes = permission_service.get_allowed_scopes("scoped_model")
        assert "preferences" in scopes
        assert "notes" in scopes
        
        # Test unknown model
        scopes = permission_service.get_allowed_scopes("unknown_model")
        assert len(scopes) == 0  # Assuming allow_unknown_models is False
    
    def test_check_permission(self, setup_database):
        """Test checking permissions for context access."""
        # Create a context entry
        entry = vault_service.save_context(
            content="Test content for permission check",
            context_type=ContextType.PREFERENCE,
            tags=["test"]
        )
        
        # Create permission that allows preferences
        permission_service.create_permission_rule(
            model_id="allowed_model",
            scopes=["preferences"]
        )
        
        # Test allowed access
        allowed, reason, perm_ids = permission_service.check_permission(
            "allowed_model", entry
        )
        assert allowed is True
        assert "granted" in reason.lower() or "allow" in reason.lower()
        
        # Test denied access (no permission)
        allowed, reason, perm_ids = permission_service.check_permission(
            "denied_model", entry
        )
        assert allowed is False
        assert "no permissions" in reason.lower()
    
    def test_apply_permission_filters(self, setup_database):
        """Test applying permission filters to context entries."""
        # Create test entries
        entry1 = vault_service.save_context(
            content="Preference entry",
            context_type=ContextType.PREFERENCE,
            tags=["pref"]
        )
        entry2 = vault_service.save_context(
            content="Note entry",
            context_type=ContextType.NOTE,
            tags=["note"]
        )
        entry3 = vault_service.save_context(
            content="Text entry",
            context_type=ContextType.TEXT,
            tags=["text"]
        )
        
        all_entries = [entry1, entry2, entry3]
        
        # Create permission that only allows preferences and notes
        permission_service.create_permission_rule(
            model_id="limited_model",
            scopes=["preferences", "notes"]
        )
        
        # Apply filters
        filtered_entries = permission_service.apply_permission_filters(
            all_entries, "limited_model"
        )
        
        # Should have at most 2 entries (preference and note)
        assert len(filtered_entries) <= 2
        
        # Verify only allowed types are included
        for entry in filtered_entries:
            assert entry.context_type in [ContextType.PREFERENCE, ContextType.NOTE]
    
    def test_get_permission_summary(self, setup_database):
        """Test getting permission summary for a model."""
        # Create permission
        permission_service.create_permission_rule(
            model_id="summary_model",
            scopes=["preferences", "notes"],
            rules={"max_entries": 25}
        )
        
        summary = permission_service.get_permission_summary("summary_model")
        
        assert summary["model_id"] == "summary_model"
        assert summary["has_permissions"] is True
        assert summary["total_permissions"] >= 1
        assert summary["active_permissions"] >= 1
        assert "preferences" in summary["allowed_scopes"]
        assert "notes" in summary["allowed_scopes"]
        assert summary["access_level"] == "limited"
    
    def test_validate_model_access(self, setup_database):
        """Test validating model access for queries."""
        # Create permission
        permission_service.create_permission_rule(
            model_id="query_model",
            scopes=["preferences"],
            rules={"max_entries": 10}
        )
        
        # Test valid query
        query = {
            "context_types": [ContextType.PREFERENCE],
            "limit": 20
        }
        
        allowed, reason, modified_query = permission_service.validate_model_access(
            "query_model", query
        )
        
        assert allowed is True
        assert modified_query["limit"] == 10  # Should be limited by permission
        
        # Test invalid query (requesting disallowed type)
        query = {
            "context_types": [ContextType.FILE],
            "limit": 5
        }
        
        allowed, reason, modified_query = permission_service.validate_model_access(
            "query_model", query
        )
        
        assert allowed is False
        assert "not allowed" in reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
