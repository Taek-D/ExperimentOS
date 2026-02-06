from typing import List, Dict, Any, Optional
import httpx
import logging

from .base import (
    IntegrationProvider, 
    ExperimentSummary, 
    IntegrationResult, 
    IntegrationError,
    RetryPolicy
)
from .registry import registry
from .schema import IntegrationVariant

logger = logging.getLogger(__name__)

class HackleProvider(IntegrationProvider):
    """
    Hackle integration provider.
    
    NOTE: As of Feb 2026, Hackle does not provide a public Management API 
    for listing experiments or fetching aggregated stats programmatically 
    (only Decision/Track APIs exist).
    
    This implementation serves as a placeholder structure.
    """
    # Placeholder base URL
    BASE_URL = "https://api.hackle.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Hypothetical headers
        self.headers = {
            "X-HACKLE-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    @property
    def provider_name(self) -> str:
        return "hackle"

    def list_experiments(self) -> List[ExperimentSummary]:
        """
        List experiments from Hackle.
        
        TODO: Implement when Hackle releases Open API for experiment listing.
        """
        # Explicitly behave as "Not Supported" to UI
        # raising IntegrationError with a clear message allow usage of try-except blocks upstream if needed
        # or displaying the message to user.
        raise IntegrationError(
            "Listing experiments is not supported by Hackle Public API currently. "
            "Please check Hackle documentation or contact support.",
            provider=self.provider_name
        )

    def fetch_experiment(self, experiment_id: str) -> IntegrationResult:
        """
        Fetch detailed experiment results from Hackle.
        
        TODO: Implement when Hackle releases Open API for result fetching.
        """
        # Placeholder for future implementation
        # url = f"{self.BASE_URL}/experiments/{experiment_id}/results"
        
        raise IntegrationError(
            "Fetching experiment results is not supported by Hackle Public API currently.",
            provider=self.provider_name
        )

# Register the provider
registry.register("hackle", HackleProvider)
