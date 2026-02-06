from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
import pytest

client = TestClient(app)

def test_list_statsig_experiments_api_success():
    mock_response_data = {
        "message": "success",
        "data": [
            {
                "id": "exp_api_123",
                "name": "API Test Experiment",
                "status": "active",
                "lastModifiedTime": 1708000000000
            }
        ]
    }

    # Mock httpx.Client at the source where StatsigProvider uses it
    # Note: We need to patch where StatsigProvider is defined or imported mechanism
    # Since StatsigProvider imports httpx, we patch httpx.Client
    with patch("src.experimentos.integrations.statsig.httpx.Client") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_client = mock_instance.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response

        headers = {"X-Integration-Api-Key": "test-api-key"}
        response = client.get("/api/integrations/statsig/experiments", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "exp_api_123"
        assert data[0]["provider"] == "statsig"

def test_list_statsig_experiments_api_auth_error():
    with patch("src.experimentos.integrations.statsig.httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response

        headers = {"X-Integration-Api-Key": "invalid-key"}
        response = client.get("/api/integrations/statsig/experiments", headers=headers)
        
        # ProviderAuthError is mapped to 401 in router
        assert response.status_code == 401
        assert "Invalid Statsig API Key" in response.json()["detail"]

def test_list_statsig_experiments_api_missing_key():
    # Attempt without header
    response = client.get("/api/integrations/statsig/experiments")
    assert response.status_code == 401
    assert "X-Integration-Api-Key header is required" in response.json()["detail"]

def test_analyze_statsig_experiment_success():
    # Mock data for fetch_experiment
    mock_data = {
        "message": "success",
        "data": {
            "id": "exp_456",
            "results": [
                {
                    "name": "Control",
                    "exposures": 1000,
                    "conversions": 100,
                    "metrics": {"revenue": 5000.0}
                },
                {
                    "name": "Treatment",
                    "exposures": 1000,
                    "conversions": 120,
                    "metrics": {"revenue": 6000.0}
                }
            ]
        }
    }

    with patch("httpx.Client") as mock_client_cls:
        # Mocking for fetch_experiment
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        
        mock_client.get.return_value = mock_response

        # Request
        response = client.get(
            "/api/integrations/statsig/experiments/exp_456/analyze",
            headers={"X-Integration-Api-Key": "test_key"}
        )
        
        assert response.status_code == 200
        json_resp = response.json()
        
        assert json_resp["status"] == "success"
        assert json_resp["experiment_id"] == "exp_456"
        assert json_resp["provider"] == "statsig"
        
        # Verify primary result structure (depends on calculate_primary implementation)
        # Assuming it returns a dict with analysis
        assert "primary_result" in json_resp
        assert json_resp["primary_result"] is not None
        
        # Optional: Check if metrics are passed through
        # This requires knwoledge of calculate_primary output structure
        # Use simple presence check for now

