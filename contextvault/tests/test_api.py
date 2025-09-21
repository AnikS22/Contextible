"""Tests for ContextVault API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contextvault.main import app
from contextvault.database import Base, get_db_session
from contextvault.models import ContextEntry, Permission, ContextType


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_contextvault.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_session] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_context_entry():
    """Create a sample context entry for testing."""
    return {
        "content": "This is a test context entry",
        "context_type": "text",
        "source": "test",
        "tags": ["test", "sample"],
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_permission():
    """Create a sample permission for testing."""
    return {
        "model_id": "test_model",
        "model_name": "Test Model",
        "scope": "preferences,notes",
        "description": "Test permission",
        "rules": {"max_entries": 10, "max_age_days": 30}
    }


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["version"] == "0.1.0"
    
    def test_liveness_probe(self, client):
        """Test liveness probe."""
        response = client.get("/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_readiness_probe(self, client):
        """Test readiness probe."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
    
    def test_metrics(self, client):
        """Test metrics endpoint."""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "database" in data
        assert "system" in data
        assert "application" in data


class TestContextEndpoints:
    """Test context management endpoints."""
    
    def test_create_context_entry(self, client, sample_context_entry):
        """Test creating a context entry."""
        response = client.post("/api/context/", json=sample_context_entry)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["content"] == sample_context_entry["content"]
        assert data["context_type"] == sample_context_entry["context_type"]
        assert data["tags"] == sample_context_entry["tags"]
    
    def test_get_context_entries(self, client, sample_context_entry):
        """Test getting context entries."""
        # First create an entry
        create_response = client.post("/api/context/", json=sample_context_entry)
        assert create_response.status_code == 200
        
        # Then get entries
        response = client.get("/api/context/")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert len(data["entries"]) >= 1
    
    def test_get_context_entry_by_id(self, client, sample_context_entry):
        """Test getting a specific context entry."""
        # Create an entry
        create_response = client.post("/api/context/", json=sample_context_entry)
        entry_id = create_response.json()["id"]
        
        # Get the entry
        response = client.get(f"/api/context/{entry_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == entry_id
        assert data["content"] == sample_context_entry["content"]
    
    def test_update_context_entry(self, client, sample_context_entry):
        """Test updating a context entry."""
        # Create an entry
        create_response = client.post("/api/context/", json=sample_context_entry)
        entry_id = create_response.json()["id"]
        
        # Update the entry
        update_data = {"content": "Updated content", "tags": ["updated"]}
        response = client.put(f"/api/context/{entry_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["tags"] == ["updated"]
    
    def test_delete_context_entry(self, client, sample_context_entry):
        """Test deleting a context entry."""
        # Create an entry
        create_response = client.post("/api/context/", json=sample_context_entry)
        entry_id = create_response.json()["id"]
        
        # Delete the entry
        response = client.delete(f"/api/context/{entry_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/context/{entry_id}")
        assert get_response.status_code == 404
    
    def test_search_context_entries(self, client, sample_context_entry):
        """Test searching context entries."""
        # Create an entry
        client.post("/api/context/", json=sample_context_entry)
        
        # Search for it
        response = client.get("/api/context/search/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) >= 1
    
    def test_context_stats(self, client, sample_context_entry):
        """Test getting context statistics."""
        # Create an entry
        client.post("/api/context/", json=sample_context_entry)
        
        # Get stats
        response = client.get("/api/context/stats/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_entries" in data
        assert "entries_by_type" in data
        assert data["total_entries"] >= 1
    
    def test_get_tags(self, client, sample_context_entry):
        """Test getting all tags."""
        # Create an entry with tags
        client.post("/api/context/", json=sample_context_entry)
        
        # Get tags
        response = client.get("/api/context/tags/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert "test" in data
        assert "sample" in data


class TestPermissionEndpoints:
    """Test permission management endpoints."""
    
    def test_create_permission(self, client, sample_permission):
        """Test creating a permission."""
        response = client.post("/api/permissions/", json=sample_permission)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["model_id"] == sample_permission["model_id"]
        assert data["scope"] == sample_permission["scope"]
    
    def test_get_permissions(self, client, sample_permission):
        """Test getting permissions."""
        # Create a permission
        client.post("/api/permissions/", json=sample_permission)
        
        # Get permissions
        response = client.get("/api/permissions/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_permission_by_id(self, client, sample_permission):
        """Test getting a specific permission."""
        # Create a permission
        create_response = client.post("/api/permissions/", json=sample_permission)
        permission_id = create_response.json()["id"]
        
        # Get the permission
        response = client.get(f"/api/permissions/{permission_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == permission_id
        assert data["model_id"] == sample_permission["model_id"]
    
    def test_update_permission(self, client, sample_permission):
        """Test updating a permission."""
        # Create a permission
        create_response = client.post("/api/permissions/", json=sample_permission)
        permission_id = create_response.json()["id"]
        
        # Update the permission
        update_data = {"scope": "all", "description": "Updated permission"}
        response = client.put(f"/api/permissions/{permission_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["scope"] == "all"
        assert data["description"] == "Updated permission"
    
    def test_delete_permission(self, client, sample_permission):
        """Test deleting a permission."""
        # Create a permission
        create_response = client.post("/api/permissions/", json=sample_permission)
        permission_id = create_response.json()["id"]
        
        # Delete the permission
        response = client.delete(f"/api/permissions/{permission_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/permissions/{permission_id}")
        assert get_response.status_code == 404
    
    def test_check_permission(self, client, sample_permission, sample_context_entry):
        """Test checking permissions."""
        # Create a permission and context entry
        perm_response = client.post("/api/permissions/", json=sample_permission)
        context_response = client.post("/api/context/", json=sample_context_entry)
        
        context_id = context_response.json()["id"]
        
        # Check permission
        check_data = {
            "model_id": sample_permission["model_id"],
            "context_entry_id": context_id,
            "scope": "preferences"
        }
        response = client.post("/api/permissions/check", json=check_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "allowed" in data
        assert "reason" in data
        assert isinstance(data["allowed"], bool)
    
    def test_model_permissions_summary(self, client, sample_permission):
        """Test getting model permissions summary."""
        # Create a permission
        client.post("/api/permissions/", json=sample_permission)
        
        # Get summary
        response = client.get(f"/api/permissions/models/{sample_permission['model_id']}/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["model_id"] == sample_permission["model_id"]
        assert "total_permissions" in data
        assert "allowed_scopes" in data
    
    def test_get_all_model_permissions(self, client, sample_permission):
        """Test getting all model permissions."""
        # Create a permission
        client.post("/api/permissions/", json=sample_permission)
        
        # Get all model permissions
        response = client.get("/api/permissions/models/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["model_id"] == sample_permission["model_id"]


class TestRootEndpoints:
    """Test root and info endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "ContextVault"
        assert data["version"] == "0.1.0"
    
    def test_info_endpoint(self, client):
        """Test info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "application" in data
        assert "api" in data
        assert "configuration" in data
        assert "environment" in data


class TestErrorHandling:
    """Test error handling."""
    
    def test_not_found_context_entry(self, client):
        """Test 404 for non-existent context entry."""
        response = client.get("/api/context/nonexistent-id")
        assert response.status_code == 404
    
    def test_not_found_permission(self, client):
        """Test 404 for non-existent permission."""
        response = client.get("/api/permissions/nonexistent-id")
        assert response.status_code == 404
    
    def test_invalid_context_data(self, client):
        """Test validation error for invalid context data."""
        invalid_data = {"content": ""}  # Empty content should fail
        response = client.post("/api/context/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_permission_data(self, client):
        """Test validation error for invalid permission data."""
        invalid_data = {"model_id": ""}  # Empty model_id should fail
        response = client.post("/api/permissions/", json=invalid_data)
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
