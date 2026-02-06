import pytest
from fastapi.testclient import TestClient
from backend.main import app
from src.experimentos.integrations.registry import registry
from src.experimentos.integrations.dummy import DummyProvider

# Register dummy provider for testing ensures it's available
registry.register("dummy", DummyProvider)

client = TestClient(app)

class TestIntegrationAPI:
    def test_missing_api_key(self):
        """Test that missing header returns 401."""
        response = client.get("/api/integrations/dummy/experiments")
        assert response.status_code == 401
        assert "X-Integration-Api-Key header is required" in response.json()["detail"]

    def test_invalid_api_key(self):
        """Test that invalid key for dummy provider returns 401."""
        response = client.get(
            "/api/integrations/dummy/experiments",
            headers={"X-Integration-Api-Key": "invalid_key"}
        )
        assert response.status_code == 401
        assert "Invalid API Key" in response.json()["detail"]

    def test_list_experiments_success(self):
        """Test listing experiments with valid key."""
        response = client.get(
            "/api/integrations/dummy/experiments",
            headers={"X-Integration-Api-Key": "valid_key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == "exp_001"
        assert data[0]["provider"] == "dummy"

    def test_unknown_provider(self):
        """Test requesting a non-existent provider returns 404."""
        response = client.get(
            "/api/integrations/unknown/experiments",
            headers={"X-Integration-Api-Key": "valid_key"}
        )
        assert response.status_code == 404
        assert "Provider 'unknown' not found" in response.json()["detail"]

    def test_analyze_experiment_success(self):
        """Test full analysis flow for a valid experiment."""
        response = client.get(
            "/api/integrations/dummy/experiments/exp_001/analyze",
            headers={"X-Integration-Api-Key": "valid_key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["experiment_id"] == "exp_001"
        assert "primary_result" in data
        assert "relative_lift" in data["primary_result"]
        
    def test_analyze_experiment_not_found(self):
        """Test analyzing a non-existent experiment ID."""
        response = client.get(
            "/api/integrations/dummy/experiments/exp_999/analyze",
            headers={"X-Integration-Api-Key": "valid_key"}
        )
        assert response.status_code == 404  # ProviderNotFoundError from fetch_experiment

    def test_analyze_experiment_fetch_error(self):
        """Test integration fetch error (simulated)."""
        response = client.get(
            "/api/integrations/dummy/experiments/exp_error/analyze",
            headers={"X-Integration-Api-Key": "valid_key"}
        )
        assert response.status_code == 502
        assert "Integration Error" in response.json()["detail"]
