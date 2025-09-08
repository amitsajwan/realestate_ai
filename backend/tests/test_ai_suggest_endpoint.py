#!/usr/bin/env python3
"""
Tests for AI suggest endpoint fixes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.routes import AIPropertySuggestRequest


class TestAISuggestEndpointFixes:
    """Test suite for AI suggest endpoint fixes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_ai_suggest_data(self):
        """Valid AI suggest request data"""
        return {
            "address": "123 Main Street, City Center",
            "property_type": "Apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 1200,
            "price": "₹50,00,000",
            "user_profile": {
                "experienceLevel": "intermediate",
                "specialization": "residential",
                "priceRange": "mid-range"
            },
            "agent_profile": {
                "specialization": "residential",
                "experience_level": "intermediate",
                "brand_name": "Test Realty",
                "tagline": "Your trusted real estate partner"
            }
        }
    
    def test_ai_suggest_request_model(self, valid_ai_suggest_data):
        """Test that AIPropertySuggestRequest model works correctly"""
        # Test that the model accepts the data without validation errors
        request = AIPropertySuggestRequest(**valid_ai_suggest_data)
        
        assert request.address == "123 Main Street, City Center"
        assert request.property_type == "Apartment"
        assert request.bedrooms == 3
        assert request.bathrooms == 2
        assert request.area == 1200
        assert request.price == "₹50,00,000"
        assert request.user_profile["experienceLevel"] == "intermediate"
        assert request.agent_profile["specialization"] == "residential"
    
    def test_ai_suggest_request_with_minimal_data(self):
        """Test that AIPropertySuggestRequest works with minimal data"""
        minimal_data = {
            "address": "123 Main St",
            "property_type": "House"
        }
        
        request = AIPropertySuggestRequest(**minimal_data)
        
        assert request.address == "123 Main St"
        assert request.property_type == "House"
        assert request.bedrooms == 2  # Default value
        assert request.bathrooms == 2  # Default value
        assert request.area == 1000  # Default value
        assert request.price is None
        assert request.user_profile is None
        assert request.agent_profile is None
    
    def test_ai_suggest_request_backward_compatibility(self):
        """Test backward compatibility with old field names"""
        old_format_data = {
            "location": "Bandra West, Mumbai",
            "property_type": "Apartment",
            "budget": "₹60,00,000",
            "requirements": "Modern amenities"
        }
        
        request = AIPropertySuggestRequest(**old_format_data)
        
        assert request.location == "Bandra West, Mumbai"
        assert request.property_type == "Apartment"
        assert request.budget == "₹60,00,000"
        assert request.requirements == "Modern amenities"
    
    def test_ai_suggest_endpoint_success(self, client, valid_ai_suggest_data):
        """Test successful AI suggest endpoint call"""
        # Make request
        response = client.post("/api/v1/property/ai_suggest", json=valid_ai_suggest_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert len(response_data["data"]) == 1
        assert "title" in response_data["data"][0]
        assert "price" in response_data["data"][0]
    
    def test_ai_suggest_endpoint_validation_error(self, client):
        """Test AI suggest endpoint with invalid data"""
        invalid_data = {
            "address": "",  # Empty address
            "property_type": "",  # Empty property type
            "bedrooms": -1,  # Invalid bedrooms
            "bathrooms": -1,  # Invalid bathrooms
            "area": -100  # Invalid area
        }
        
        # Make request
        response = client.post("/api/v1/property/ai_suggest", json=invalid_data)
        
        # Should still work with default values
        assert response.status_code == 200
    
    def test_ai_suggest_endpoint_missing_data(self, client):
        """Test AI suggest endpoint with missing data"""
        # Make request with no data
        response = client.post("/api/v1/property/ai_suggest", json={})
        
        # Should work with default values
        assert response.status_code == 200
    
    def test_ai_suggest_request_model_optional_fields(self):
        """Test that all fields in AIPropertySuggestRequest are optional"""
        # Test with completely empty data
        request = AIPropertySuggestRequest()
        
        assert request.address is None
        assert request.location is None
        assert request.property_type == "Apartment"  # Default value
        assert request.bedrooms == 2  # Default value
        assert request.bathrooms == 2  # Default value
        assert request.area == 1000  # Default value
        assert request.price is None
        assert request.budget is None
        assert request.requirements is None
        assert request.user_profile is None
        assert request.agent_profile is None
    
    def test_ai_suggest_request_field_types(self, valid_ai_suggest_data):
        """Test that field types are correctly handled"""
        request = AIPropertySuggestRequest(**valid_ai_suggest_data)
        
        # Test numeric fields
        assert isinstance(request.bedrooms, int)
        assert isinstance(request.bathrooms, int)
        assert isinstance(request.area, int)
        
        # Test string fields
        assert isinstance(request.address, str)
        assert isinstance(request.property_type, str)
        assert isinstance(request.price, str)
        
        # Test dict fields
        assert isinstance(request.user_profile, dict)
        assert isinstance(request.agent_profile, dict)
    
    def test_price_parsing_various_formats(self):
        """Test that various price formats are handled correctly"""
        test_cases = [
            # (input_price, expected_parsed_value)
            ("₹50,00,000", "₹50,00,000"),
            ("5000000", "5000000"),
            ("50L", "50L"),
            ("5Cr", "5Cr"),
            ("₹75,00,000", "₹75,00,000"),
            ("₹1,20,00,000", "₹1,20,00,000"),
            ("₹2.5Cr", "₹2.5Cr"),
            ("₹85L", "₹85L"),
        ]
        
        for input_price, expected in test_cases:
            request = AIPropertySuggestRequest(price=input_price)
            assert request.price == expected
    
    def test_price_parsing_with_different_property_types(self):
        """Test that default prices are calculated based on property type and area"""
        test_cases = [
            # (property_type, area, expected_min_price, expected_max_price)
            ("Apartment", 1000, 4000000, 6000000),  # 4000-6000 per sqft
            ("House", 1200, 4000000, 6000000),      # 4000-6000 per sqft
            ("Villa", 2000, 14000000, 18000000),    # 7000-9000 per sqft
            ("Commercial", 1500, 8000000, 10000000), # 5000-7000 per sqft
            ("Plot", 500, 800000, 1200000),         # 1500-2500 per sqft
        ]
        
        for property_type, area, min_price, max_price in test_cases:
            request = AIPropertySuggestRequest(
                property_type=property_type,
                area=area
            )
            assert request.property_type == property_type
            assert request.area == area
    
    def test_price_parsing_edge_cases(self):
        """Test edge cases in price parsing"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "invalid",  # Invalid format
            "₹",  # Just currency symbol
            "L",  # Just suffix
            "Cr",  # Just suffix
        ]
        
        for edge_case in edge_cases:
            request = AIPropertySuggestRequest(price=edge_case)
            assert request.price == edge_case
    
    def test_ai_suggest_with_calculated_default_price(self, client):
        """Test AI suggest with calculated default price when no price provided"""
        data_without_price = {
            "address": "123 Main Street",
            "property_type": "Apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 1200,
            # No price provided - should use calculated default
        }
        
        response = client.post("/api/v1/property/ai_suggest", json=data_without_price)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert len(response_data["data"]) > 0
        
        # The price should be calculated based on area and property type
        suggested_price = response_data["data"][0]["price"]
        assert isinstance(suggested_price, (int, float))
        assert suggested_price > 0
    
    def test_ai_suggest_with_various_price_formats(self, client):
        """Test AI suggest with various price formats"""
        price_formats = [
            "₹50,00,000",
            "5000000",
            "50L",
            "5Cr",
            "₹75,00,000"
        ]
        
        for price_format in price_formats:
            data = {
                "address": "123 Main Street",
                "property_type": "Apartment",
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 1200,
                "price": price_format
            }
            
            response = client.post("/api/v1/property/ai_suggest", json=data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert len(response_data["data"]) > 0
            
            # The returned price should be a number, not a string
            suggested_price = response_data["data"][0]["price"]
            assert isinstance(suggested_price, (int, float))
            assert suggested_price > 0


if __name__ == "__main__":
    pytest.main([__file__])
