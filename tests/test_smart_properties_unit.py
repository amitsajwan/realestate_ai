"""
Unit Tests for Smart Properties API Endpoints
Uses pytest framework for detailed API testing
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from api.endpoints.smart_properties import generate_simple_ai_content, SmartPropertyCreate
from repositories.property_repository import PropertyRepository


class TestSmartPropertiesUnit:
    """Unit tests for Smart Properties components"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_generate_simple_ai_content_just_listed(self):
        """Test AI content generation for just_listed template"""
        property_data = {
            "address": "123 Test Street, Mumbai",
            "price": "₹2.5 Crore",
            "property_type": "apartment",
            "bedrooms": "3",
            "bathrooms": "2",
            "features": "Sea view, modern kitchen"
        }
        
        content = generate_simple_ai_content(property_data, "just_listed", "en")
        
        # Assertions
        assert "JUST LISTED" in content
        assert property_data["address"] in content
        assert property_data["price"] in content
        assert "3 bedrooms" in content
        assert "2 bathrooms" in content
        assert "#JustListed" in content
        assert len(content) > 100  # Ensure content is substantial
    
    def test_generate_simple_ai_content_open_house(self):
        """Test AI content generation for open_house template"""
        property_data = {
            "address": "456 Park Road, Delhi",
            "price": "₹1.8 Crore",
            "property_type": "villa",
            "bedrooms": "4",
            "bathrooms": "3",
            "features": "Garden, parking"
        }
        
        content = generate_simple_ai_content(property_data, "open_house", "en")
        
        # Assertions
        assert "OPEN HOUSE" in content
        assert property_data["address"] in content
        assert property_data["price"] in content
        assert "4 bed" in content
        assert "3 bath" in content
        assert "#OpenHouse" in content
        assert "This weekend" in content
    
    def test_generate_simple_ai_content_default_template(self):
        """Test AI content generation for default template"""
        property_data = {
            "address": "789 Main Street, Bangalore",
            "price": "₹3.2 Crore",
            "property_type": "penthouse",
            "bedrooms": "5",
            "bathrooms": "4",
            "features": "Luxury amenities"
        }
        
        content = generate_simple_ai_content(property_data, "featured", "en")
        
        # Assertions
        assert "FEATURED PROPERTY" in content
        assert property_data["address"] in content
        assert property_data["price"] in content
        assert "5 bed" in content
        assert "4 bath" in content
        assert "#PropertyListing" in content
    
    def test_smart_property_create_model_validation(self):
        """Test SmartPropertyCreate model validation"""
        # Valid data
        valid_data = {
            "address": "123 Test Street",
            "price": "₹2.5 Crore",
            "property_type": "apartment",
            "bedrooms": "3",
            "bathrooms": "2",
            "features": "Modern amenities",
            "template": "just_listed",
            "language": "en"
        }
        
        property_create = SmartPropertyCreate(**valid_data)
        assert property_create.address == "123 Test Street"
        assert property_create.price == "₹2.5 Crore"
        assert property_create.auto_generate is True  # Default value
        
        # Test with minimal required data
        minimal_data = {
            "address": "456 Minimal Street",
            "price": "₹1.0 Crore", 
            "property_type": "condo"
        }
        
        minimal_property = SmartPropertyCreate(**minimal_data)
        assert minimal_property.bedrooms is None
        assert minimal_property.template == "just_listed"  # Default value
    
    @pytest.mark.asyncio
    async def test_property_repository_operations(self):
        """Test PropertyRepository CRUD operations"""
        repo = PropertyRepository()
        
        # Test creating a property
        property_data = {
            "title": "Test Property",
            "address": "123 Repository Test Street",
            "price": "₹2.0 Crore",
            "property_type": "apartment",
            "bedrooms": "2",
            "bathrooms": "1",
            "agent_id": "test-agent-123"
        }
        
        created = await repo.create_property(property_data)
        assert created["address"] == property_data["address"]
        assert created["price"] == property_data["price"]
        assert "id" in created
        assert "created_at" in created
        
        property_id = created["id"]
        
        # Test getting the property
        retrieved = await repo.get_property(property_id)
        assert retrieved is not None
        assert retrieved["address"] == property_data["address"]
        
        # Test updating the property
        updates = {"ai_content": "Updated AI content"}
        updated = await repo.update_property(property_id, updates)
        assert updated is not None
        assert updated["ai_content"] == "Updated AI content"
        assert "updated_at" in updated
        
        # Test getting properties by agent
        agent_properties = await repo.get_properties_by_agent("test-agent-123")
        assert len(agent_properties) >= 1
        assert any(prop["id"] == property_id for prop in agent_properties)
        
        # Test deleting the property
        deleted = await repo.delete_property(property_id, "test-agent-123")
        assert deleted is True
        
        # Verify deletion
        deleted_prop = await repo.get_property(property_id)
        assert deleted_prop is None


class TestSmartPropertiesIntegration:
    """Integration tests for Smart Properties API"""
    
    def setup_method(self):
        """Set up test client with authentication"""
        self.client = TestClient(app)
        # Create a simple auth header for testing
        self.auth_header = {"Authorization": "Bearer demo.token.signature"}
    
    def test_create_property_endpoint(self):
        """Test POST /api/smart-properties endpoint"""
        property_data = {
            "address": "123 Integration Test Street",
            "price": "₹2.5 Crore",
            "property_type": "apartment",
            "bedrooms": "3",
            "bathrooms": "2",
            "features": "Integration test property",
            "template": "just_listed",
            "auto_generate": True
        }
        
        response = self.client.post(
            "/api/smart-properties",
            json=property_data,
            headers=self.auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["address"] == property_data["address"]
        assert data["price"] == property_data["price"]
        assert data["property_type"] == property_data["property_type"]
        assert "ai_content" in data
        assert len(data["ai_content"]) > 50
        assert "id" in data
        assert "created_at" in data
    
    def test_get_properties_endpoint(self):
        """Test GET /api/smart-properties endpoint"""
        response = self.client.get(
            "/api/smart-properties/",
            headers=self.auth_header
        )
        
        assert response.status_code == 200
        properties = response.json()
        assert isinstance(properties, list)
        
        # Properties should include demo data
        if properties:
            prop = properties[0]
            required_fields = ["id", "address", "price", "property_type"]
            for field in required_fields:
                assert field in prop
    
    def test_get_properties_without_auth(self):
        """Test that authentication is required"""
        response = self.client.get("/api/smart-properties/")
        assert response.status_code == 401
    
    def test_create_property_without_auth(self):
        """Test that property creation requires authentication"""
        property_data = {
            "address": "Unauthorized Test Street",
            "price": "₹1.0 Crore",
            "property_type": "apartment"
        }
        
        response = self.client.post("/api/smart-properties", json=property_data)
        assert response.status_code == 401
    
    def test_create_property_invalid_data(self):
        """Test property creation with invalid data"""
        invalid_data = {
            "price": "₹1.0 Crore",
            "property_type": "apartment"
            # Missing required 'address' field
        }
        
        response = self.client.post(
            "/api/smart-properties",
            json=invalid_data,
            headers=self.auth_header
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
