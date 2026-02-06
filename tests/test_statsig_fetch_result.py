import pytest
from unittest.mock import MagicMock, patch
from src.experimentos.integrations.statsig import StatsigProvider
from src.experimentos.integrations.base import ProviderAuthError, IntegrationError
from src.experimentos.integrations.cache import reset_cache_instance

@pytest.fixture(autouse=True)
def clean_cache():
    reset_cache_instance()

@pytest.fixture
def statsig_provider():
    return StatsigProvider(api_key="test_secret_key")

def test_fetch_experiment_success(statsig_provider):
    mock_data = {
        "message": "success",
        "data": {
            "id": "exp_123",
            "results": [
                {
                    "name": "Control",
                    "exposures": 1000,
                    "conversions": 100,
                    "metrics": {"revenue": 5000.0, "clicks": 200.0}
                },
                {
                    "name": "Treatment",
                    "exposures": 1000,
                    "conversions": 120, # Higher conversion
                    "metrics": {"revenue": 6000.0, "clicks": 250.0}
                }
            ]
        }
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        
        mock_client.get.return_value = mock_response

        # Execute
        result = statsig_provider.fetch_experiment("exp_123")

        # Verify Integrity
        assert result.experiment_id == "exp_123"
        assert len(result.variants) == 2
        
        control = result.variants[0]
        assert control.name == "Control"
        assert control.users == 1000
        assert control.conversions == 100
        assert control.metrics["revenue"] == 5000.0
        
        treatment = result.variants[1]
        assert treatment.name == "Treatment"
        assert treatment.conversions == 120 

def test_fetch_experiment_auth_error(statsig_provider):
    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client.get.return_value = mock_response

        with pytest.raises(ProviderAuthError):
            statsig_provider.fetch_experiment("exp_123")

def test_fetch_experiment_no_results(statsig_provider):
    mock_data = {
        "message": "success",
        "data": {
            "id": "exp_empty",
            "results": []
        }
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        
        mock_client.get.return_value = mock_response

        with pytest.raises(IntegrationError) as excinfo:
            statsig_provider.fetch_experiment("exp_empty")
        
        assert "No results found" in str(excinfo.value)
