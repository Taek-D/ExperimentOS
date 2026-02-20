from .base import IntegrationProvider, ExperimentSummary, ProviderNotFoundError, IntegrationError, ProviderAuthError
from .schema import IntegrationResult, IntegrationVariant

class DummyProvider(IntegrationProvider):
    """
    A dummy provider that returns static data for testing purposes.
    No real API calls are made.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Check for a specific 'magic' key to simulate auth failure if needed
        if api_key == "invalid_key":
             raise ProviderAuthError("Invalid API Key for Dummy Provider", provider="dummy")

    @property
    def provider_name(self) -> str:
        return "dummy"

    def list_experiments(self) -> list[ExperimentSummary]:
        return [
            ExperimentSummary(id="exp_001", name="Checkout Redesign", status="running"),
            ExperimentSummary(id="exp_002", name="Search Algorithm V2", status="stopped"),
            ExperimentSummary(id="exp_error", name="Simulate Error", status="running"), # To test error flow
        ]

    def fetch_experiment(self, experiment_id: str) -> IntegrationResult:
        if experiment_id == "exp_error":
             raise IntegrationError("Simulated Fetch Error", provider="dummy")
             
        # Deterministic dummy data
        if experiment_id == "exp_001":
            return IntegrationResult(
                experiment_id="exp_001",
                variants=[
                    IntegrationVariant(name="control", users=1000, conversions=100, metrics={"guardrail_latency": 0.5}),
                    IntegrationVariant(name="treatment", users=1000, conversions=120, metrics={"guardrail_latency": 0.55})
                ]
            )
        elif experiment_id == "exp_002":
             return IntegrationResult(
                experiment_id="exp_002",
                variants=[
                    IntegrationVariant(name="A", users=500, conversions=50),
                    IntegrationVariant(name="B", users=500, conversions=60)
                ]
            )
        else:
            raise ProviderNotFoundError(f"Experiment {experiment_id} not found", provider="dummy")

# Register the dummy provider immediately when this module is imported
# In a real app, this might be done in an __init__.py or main startup
from .registry import registry
registry.register("dummy", DummyProvider)
