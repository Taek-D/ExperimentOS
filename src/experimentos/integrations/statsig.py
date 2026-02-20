from typing import Any
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from .base import (
    IntegrationProvider, 
    ExperimentSummary, 
    IntegrationResult, 
    ProviderAuthError, 
    IntegrationError,
    RetryPolicy
)

from .schema import IntegrationVariant, IntegrationResult
from .registry import registry
from .cache import get_cache
from .retry import retry_request

class StatsigProvider(IntegrationProvider):
    """
    Statsig integration provider using the Console API.
    """
    BASE_URL = "https://statsigapi.net/console/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "statsig-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        # Timeout settings could be configurable via RetryPolicy in the future
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.cache = get_cache()

    @retry_request(max_retries=3, base_delay=0.5, backoff_factor=2.0)
    def _make_get_request(self, url: str) -> dict[str, Any]:
        """Helper to check for 401s and raise ProviderAuthError specifically."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self.headers)
            
            if response.status_code == 401:
                raise ProviderAuthError("Invalid Statsig API Key", provider=self.provider_name)
            
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    @property
    def provider_name(self) -> str:
        return "statsig"

    def list_experiments(self) -> list[ExperimentSummary]:
        """
        List experiments from Statsig.
        """
        url = f"{self.BASE_URL}/experiments"
        try:
            data = self._make_get_request(url)

            # Statsig API response format: { "message": "...", "data": [...] }
            experiments_data = data.get("data", [])
                
            summary_list = []
            for exp in experiments_data:
                # Parse timestamp if available, specifically 'lastModifiedTime'
                last_updated = None
                if "lastModifiedTime" in exp:
                    try:
                        # Statsig often returns milliseconds
                        ts = exp["lastModifiedTime"]
                        if isinstance(ts, (int, float)):
                            last_updated = datetime.fromtimestamp(ts / 1000.0)
                    except (ValueError, TypeError):
                        pass

                summary_list.append(ExperimentSummary(
                    id=exp.get("id", ""),
                    name=exp.get("name", "Unknown Experiment"),
                    status=exp.get("status", "unknown"),
                    last_updated=last_updated,
                    provider=self.provider_name
                ))
            
            return summary_list

        except ProviderAuthError:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderAuthError("Invalid Statsig API Key", provider=self.provider_name)
            raise IntegrationError(f"HTTP error: {str(e)}", provider=self.provider_name)
        except httpx.RequestError as e:
            raise IntegrationError(f"Connection error: {str(e)}", provider=self.provider_name)
        except Exception as e:
            raise IntegrationError(f"Unexpected error: {str(e)}", provider=self.provider_name)

    def fetch_experiment(self, experiment_id: str) -> IntegrationResult:
        """
        Fetch detailed experiment results from Statsig.
        Note: The endpoint '/experiments/{id}/results' is conceptual. 
        Adjust based on actual Statsig Pulse/Reports API availability.
        """
        # Conceptual endpoint for fetching results
        url = f"{self.BASE_URL}/experiments/{experiment_id}/results"
        cache_key = f"statsig:{experiment_id}:results"
        
        try:
            # Check Cache
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for experiment {experiment_id}")
                data = cached_data
            else:
                logger.info(f"Cache miss for experiment {experiment_id}, fetching from API")
                data = self._make_get_request(url)
                # Cache the raw response for 5 minutes (300 seconds)
                self.cache.set(cache_key, data, ttl=300)
            
            # Expected Mock Payload Structure for 'results':
            # {
            #   "data": {
            #     "id": "exp_id",
            #     "results": [
            #       {"name": "Control", "exposures": 1000, "conversions": 100, "metrics": {"revenue": 500.0}},
            #       {"name": "Test", "exposures": 1050, "conversions": 120, "metrics": {"revenue": 600.0}}
            #     ]
            #   }
            # }
            
            payload = data.get("data", {})
            results = payload.get("results", [])
            
            if not results:
                # Fallback or empty
                raise IntegrationError("No results found for experiment", provider=self.provider_name)

            variants = []
            for res in results:
                # Provide defaults to safely map
                variant_name = res.get("name", "unknown")
                users = res.get("exposures", 0)
                conversions = res.get("conversions", 0)
                metrics = res.get("metrics", {})
                
                variants.append(IntegrationVariant(
                    name=variant_name,
                    users=users,
                    conversions=conversions,
                    metrics=metrics
                ))
            
            return IntegrationResult(
                experiment_id=experiment_id,
                variants=variants
            )

        except ProviderAuthError:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                 raise ProviderAuthError("Invalid Statsig API Key", provider=self.provider_name)
            raise IntegrationError(f"HTTP error: {str(e)}", provider=self.provider_name)
        except httpx.RequestError as e:
            raise IntegrationError(f"Connection error: {str(e)}", provider=self.provider_name)
        except Exception as e:
            raise IntegrationError(f"Unexpected error: {str(e)}", provider=self.provider_name)

# Register the provider
registry.register("statsig", StatsigProvider)
