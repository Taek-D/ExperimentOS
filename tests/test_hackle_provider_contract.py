import pytest
from src.experimentos.integrations.hackle import HackleProvider
from src.experimentos.integrations.base import IntegrationError

@pytest.fixture
def hackle_provider():
    return HackleProvider(api_key="test_hackle_key")

def test_provider_name(hackle_provider):
    assert hackle_provider.provider_name == "hackle"

def test_list_experiments_not_implemented(hackle_provider):
    """Ensure list_experiments raises IntegrationError with specific message."""
    with pytest.raises(IntegrationError) as excinfo:
        hackle_provider.list_experiments()
    
    assert "not supported" in str(excinfo.value)
    assert excinfo.value.provider == "hackle"

def test_fetch_experiment_not_implemented(hackle_provider):
    """Ensure fetch_experiment raises IntegrationError with specific message."""
    with pytest.raises(IntegrationError) as excinfo:
        hackle_provider.fetch_experiment("exp_123")
    
    assert "not supported" in str(excinfo.value)
    assert excinfo.value.provider == "hackle"
