import pytest
from unittest.mock import patch, MagicMock
import httpx
from datetime import datetime
from src.experimentos.integrations.statsig import StatsigProvider, ProviderAuthError, IntegrationError
from src.experimentos.integrations.cache import reset_cache_instance

@pytest.fixture(autouse=True)
def clean_cache():
    reset_cache_instance()

@pytest.fixture
def statsig_provider():
    return StatsigProvider(api_key="test_secret_key")

def test_list_experiments_success(statsig_provider):
    mock_response_data = {
        "message": "success",
        "data": [
            {
                "id": "exp_abc_123",
                "name": "New Onboarding Flow",
                "status": "active",
                "lastModifiedTime": 1707000000000  # Example timestamp
            },
            {
                "id": "exp_xyz_987",
                "name": "Checkout Redesign",
                # status missing
                "lastModifiedTime": "invalid_date" # Should handle gracefully
            }
        ]
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response_data,
            raise_for_status=lambda: None
        )
        
        experiments = statsig_provider.list_experiments()
        
        assert len(experiments) == 2
        
        # Verify first experiment
        assert experiments[0].id == "exp_abc_123"
        assert experiments[0].name == "New Onboarding Flow"
        assert experiments[0].status == "active"
        assert isinstance(experiments[0].last_updated, datetime)
        assert experiments[0].provider == "statsig"
        
        # Verify second experiment (handling missing/invalid fields)
        assert experiments[1].id == "exp_xyz_987"
        assert experiments[1].status == "unknown"
        assert experiments[1].last_updated is None

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        # Configure response
        mock_response = MagicMock()
        mock_response.status_code = 401
        # Make raise_for_status do nothing
        mock_response.raise_for_status.return_value = None
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        # Make raise_for_status do nothing
        mock_response.raise_for_status.return_value = None
        
        mock_response.json.return_value = {}
        mock_client.get.return_value = mock_response
        
        with pytest.raises(ProviderAuthError):
            statsig_provider.list_experiments()

def test_list_experiments_connection_error(statsig_provider):
    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_request = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection refused", request=mock_request)
        
        try:
            statsig_provider.list_experiments()
            pytest.fail("Should have raised IntegrationError")
        except IntegrationError as e:
            if e.provider != "statsig":
                 with open("failure.log", "w") as f:
                     f.write(f"Provider mismatch. Expected 'statsig', got '{e.provider}'")
            assert e.provider == "statsig"
        except Exception as e:
            with open("failure.log", "w") as f:
                f.write(f"Raised unexpected exception: {type(e).__name__}: {e}")
            pytest.fail(f"Raised unexpected exception: {type(e).__name__}: {e}")

