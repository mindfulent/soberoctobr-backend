"""
Tests for habit templates API endpoints.

This module tests the habit template retrieval endpoints that provide
pre-configured habits for users during onboarding.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHabitTemplates:
    """Test suite for habit template endpoints."""

    def test_list_all_templates(self):
        """Test retrieving all habit templates."""
        response = client.get("/api/v1/habit-templates")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should have multiple templates
        assert len(templates) >= 10
        
        # Verify structure of first template
        template = templates[0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "type" in template
        assert "preferred_time" in template
        assert "category" in template
        assert "icon" in template
        assert template["type"] in ["binary", "counted"]

    def test_list_templates_by_category_sober_october(self):
        """Test filtering templates by sober_october category."""
        response = client.get("/api/v1/habit-templates?category=sober_october")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should have sober october templates
        assert len(templates) > 0
        
        # All should be in sober_october category
        for template in templates:
            assert template["category"] == "sober_october"
        
        # Check for specific templates
        template_ids = [t["id"] for t in templates]
        assert "no_alcohol" in template_ids

    def test_list_templates_by_category_physical_health(self):
        """Test filtering templates by physical_health category."""
        response = client.get("/api/v1/habit-templates?category=physical_health")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should have physical health templates
        assert len(templates) > 0
        
        # All should be in physical_health category
        for template in templates:
            assert template["category"] == "physical_health"
        
        # Check for specific templates
        template_ids = [t["id"] for t in templates]
        assert "exercise" in template_ids
        assert "pushups" in template_ids

    def test_list_templates_by_category_mental_wellness(self):
        """Test filtering templates by mental_wellness category."""
        response = client.get("/api/v1/habit-templates?category=mental_wellness")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should have mental wellness templates
        assert len(templates) > 0
        
        # All should be in mental_wellness category
        for template in templates:
            assert template["category"] == "mental_wellness"
        
        # Check for specific templates
        template_ids = [t["id"] for t in templates]
        assert "meditate" in template_ids
        assert "journal" in template_ids

    def test_list_templates_by_category_daily_routines(self):
        """Test filtering templates by daily_routines category."""
        response = client.get("/api/v1/habit-templates?category=daily_routines")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should have daily routine templates
        assert len(templates) > 0
        
        # All should be in daily_routines category
        for template in templates:
            assert template["category"] == "daily_routines"
        
        # Check for specific templates
        template_ids = [t["id"] for t in templates]
        assert "sleep_8hrs" in template_ids

    def test_list_templates_invalid_category_returns_all(self):
        """Test that invalid category returns all templates."""
        response = client.get("/api/v1/habit-templates?category=invalid_category")
        
        assert response.status_code == 200
        templates = response.json()
        
        # Should return all templates when category is invalid
        assert len(templates) >= 10

    def test_get_specific_template_by_id(self):
        """Test retrieving a specific template by ID."""
        response = client.get("/api/v1/habit-templates/no_alcohol")
        
        assert response.status_code == 200
        template = response.json()
        
        assert template["id"] == "no_alcohol"
        assert template["name"] == "No Alcohol"
        assert template["type"] == "binary"
        assert template["preferred_time"] == "all_day"
        assert template["category"] == "sober_october"
        assert "icon" in template

    def test_get_counted_template(self):
        """Test retrieving a counted habit template."""
        response = client.get("/api/v1/habit-templates/pushups")
        
        assert response.status_code == 200
        template = response.json()
        
        assert template["id"] == "pushups"
        assert template["type"] == "counted"
        assert template["target_count"] == 20
        assert template["preferred_time"] == "morning"

    def test_get_template_not_found(self):
        """Test retrieving non-existent template returns 404."""
        response = client.get("/api/v1/habit-templates/nonexistent")
        
        assert response.status_code == 404
        error = response.json()
        assert "not found" in error["detail"].lower()

    def test_all_templates_have_required_fields(self):
        """Test that all templates have all required fields."""
        response = client.get("/api/v1/habit-templates")
        templates = response.json()
        
        required_fields = ["id", "name", "description", "type", "preferred_time", "category", "icon"]
        
        for template in templates:
            for field in required_fields:
                assert field in template, f"Template {template.get('id')} missing field: {field}"
            
            # Type must be valid
            assert template["type"] in ["binary", "counted"]
            
            # Preferred time must be valid
            assert template["preferred_time"] in ["morning", "afternoon", "evening", "all_day"]
            
            # Category must be valid
            assert template["category"] in ["sober_october", "physical_health", "mental_wellness", "daily_routines"]

    def test_counted_templates_have_target_count(self):
        """Test that counted templates have target_count field."""
        response = client.get("/api/v1/habit-templates")
        templates = response.json()
        
        counted_templates = [t for t in templates if t["type"] == "counted"]
        
        for template in counted_templates:
            assert "target_count" in template
            if template["target_count"] is not None:
                assert template["target_count"] > 0

    def test_template_icons_present(self):
        """Test that all templates have icons."""
        response = client.get("/api/v1/habit-templates")
        templates = response.json()
        
        for template in templates:
            assert template["icon"]
            assert len(template["icon"]) > 0

    def test_specific_templates_exist(self):
        """Test that specific expected templates exist."""
        response = client.get("/api/v1/habit-templates")
        templates = response.json()
        template_ids = [t["id"] for t in templates]
        
        # Core templates that should exist
        expected_templates = [
            "no_alcohol",
            "meditate",
            "exercise",
            "pushups",
            "drink_water",
            "journal",
            "sleep_8hrs"
        ]
        
        for expected in expected_templates:
            assert expected in template_ids, f"Expected template '{expected}' not found"

