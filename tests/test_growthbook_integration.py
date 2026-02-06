import pytest
from unittest.mock import MagicMock, patch
from src.experimentos.integrations.growthbook import GrowthBookProvider
from src.experimentos.integrations.base import IntegrationError, ProviderAuthError

@pytest.fixture
def growthbook_provider():
    return GrowthBookProvider(api_key="test_gb_key")

def test_list_experiments(growthbook_provider):
    mock_response = {
        "experiments": [
            {
                "id": "exp_1",
                "name": "New Onboarding",
                "status": "running",
                "dateUpdated": "2023-10-27T10:00:00Z"
            },
            {
                "id": "exp_2",
                "name": "Checkout Flow",
                "status": "stopped"
            }
        ]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        experiments = growthbook_provider.list_experiments()
        
        assert len(experiments) == 2
        assert experiments[0].id == "exp_1"
        assert experiments[0].name == "New Onboarding"
        assert experiments[0].provider == "growthbook"
        assert experiments[1].id == "exp_2"

def test_fetch_experiment_success(growthbook_provider):
    # Mocking GrowthBook detail response with result data
    mock_response = {
        "experiment": {
            "id": "exp_123",
            "variations": [
                {"name": "Control", "key": "0"},
                {"name": "Variant A", "key": "1"}
            ],
            "results": [
                {
                    "variationId": 0,
                    "users": 1000,
                    "count": 100, # mapped to conversions
                    "revenue": 5000.0,
                    "clicks": 200
                },
                {
                    "variationId": 1,
                    "users": 1000,
                    "count": 120,
                    "revenue": 6000.0,
                    "clicks": 250
                }
            ]
        }
    }

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = growthbook_provider.fetch_experiment("exp_123")
        
        assert result.experiment_id == "exp_123"
        assert len(result.variants) == 2
        
        # Check Control
        control = result.variants[0]
        assert control.name == "Control"
        assert control.users == 1000
        assert control.conversions == 100
        assert control.metrics["revenue"] == 5000.0
        
        # Check Variant A
        variant = result.variants[1]
        assert variant.name == "Variant A"
        assert variant.users == 1000
        assert variant.conversions == 120

def test_fetch_experiment_no_results(growthbook_provider):
    mock_response = {
        "experiment": {
            "id": "exp_empty",
            "variations": [{"name": "A"}, {"name": "B"}],
            "results": []
        }
    }
    
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        # It should fallback to 0s if variations exist but no results
        result = growthbook_provider.fetch_experiment("exp_empty")
        assert len(result.variants) == 2
        assert result.variants[0].users == 0

def test_fetch_experiment_auth_error(growthbook_provider):
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.status_code = 401
        
        with pytest.raises(ProviderAuthError):
            growthbook_provider.fetch_experiment("exp_bad_auth")
