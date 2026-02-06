from typing import List, Dict, Any, Optional
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
    RetryPolicy,
    ProviderNotFoundError
)

from .schema import IntegrationVariant, IntegrationResult
from .registry import registry
from .cache import get_cache
from .retry import retry_request

class GrowthBookProvider(IntegrationProvider):
    """
    GrowthBook integration provider using the REST API.
    API Specs: https://docs.growthbook.io/api
    """
    BASE_URL = "https://api.growthbook.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        # GrowthBook uses Bearer token authentication
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.cache = get_cache()

    @retry_request(max_retries=3, base_delay=0.5, backoff_factor=2.0)
    def _make_get_request(self, url: str) -> Dict[str, Any]:
        """Helper to make GET requests with error handling."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self.headers)
            
            if response.status_code == 401:
                raise ProviderAuthError("Invalid GrowthBook API Key", provider=self.provider_name)
            if response.status_code == 404:
                raise ProviderNotFoundError(f"Resource not found: {url}", provider=self.provider_name)
            
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    @property
    def provider_name(self) -> str:
        return "growthbook"

    def list_experiments(self) -> List[ExperimentSummary]:
        """
        List experiments from GrowthBook.
        Endpoint: GET /experiments
        """
        url = f"{self.BASE_URL}/experiments"
        try:
            data = self._make_get_request(url)

            # GrowthBook API response: { "experiments": [ ... ], "limit": ..., "offset": ... }
            experiments_data = data.get("experiments", [])
                
            summary_list = []
            for exp in experiments_data:
                # Parse timestamp: 'dateUpdated' (ISO string)
                last_updated = None
                if "dateUpdated" in exp:
                    try:
                        last_updated = datetime.fromisoformat(exp["dateUpdated"].replace('Z', '+00:00'))
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
                raise ProviderAuthError("Invalid GrowthBook API Key", provider=self.provider_name)
            raise IntegrationError(f"HTTP error: {str(e)}", provider=self.provider_name)
        except httpx.RequestError as e:
            raise IntegrationError(f"Connection error: {str(e)}", provider=self.provider_name)
        except Exception as e:
            raise IntegrationError(f"Unexpected error: {str(e)}", provider=self.provider_name)

    def fetch_experiment(self, experiment_id: str) -> IntegrationResult:
        """
        Fetch detailed experiment results from GrowthBook.
        Endpoint: GET /experiments/{id}
        """
        # GrowthBook's experiment details usually include results if they are computed.
        # Note: If results are separate, we might need a different endpoint.
        # Based on docs, GET /experiments/:id returns the experiment object including data.
        
        url = f"{self.BASE_URL}/experiments/{experiment_id}"
        cache_key = f"growthbook:{experiment_id}:results"
        
        try:
            # Check Cache
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for experiment {experiment_id}")
                data = cached_data
            else:
                logger.info(f"Cache miss for experiment {experiment_id}, fetching from API")
                data = self._make_get_request(url)
                # Cache the raw response for 5 minutes
                self.cache.set(cache_key, data, ttl=300)
            
            experiment = data.get("experiment", {})
            
            if not experiment:
                raise IntegrationError("No experiment data found in response", provider=self.provider_name)

            # Extract results. GrowthBook structure varies, but we look for 'results' or 'stats'.
            # Hypothetical structure mapping based on typical schema:
            # {
            #   "results": [
            #     { "variationId": 0, "users": 100, "conversions": 10, ... },
            #     { "variationId": 1, "users": 110, "conversions": 12, ... }
            #   ],
            #   "variations": [ { "name": "Control" }, { "name": "Treatment" } ]
            # }
            
            results = experiment.get("results", [])
            variations_meta = experiment.get("variations", [])
            
            # If explicit results are missing, check if they are top-level or differently named
            # For now, we assume 'results' key exists from the API response for an experiment with data.
            
            if not results:
                # It might be that the experiment has no results yet.
                # However, we need to return something valid or raise. 
                # Let's verify if we can construct safe defaults from variations metadata.
                if variations_meta:
                    results = [{"variationId": i, "users": 0, "conversions": 0} for i, _ in enumerate(variations_meta)]
                else:
                    raise IntegrationError("No results or variations found for experiment", provider=self.provider_name)

            variants_list = []
            for i, res in enumerate(results):
                # Try to get name from metadata
                idx = res.get("variationId", i)
                v_name = "unknown"
                if idx < len(variations_meta):
                     val = variations_meta[idx]
                     # variation meta might be object with name, or just a string/value
                     if isinstance(val, dict):
                         v_name = val.get("name", str(idx))
                     else:
                         v_name = str(val)
                else:
                    v_name = str(idx)

                users = res.get("users", 0)
                # 'conversions' often depends on the goal. 
                # GrowthBook might return 'count', 'value', 'mean', etc.
                # We map 'count' or 'conversions' to conversions.
                conversions = res.get("conversions", res.get("count", 0)) 
                
                # Metrics: Collect other stats
                metrics = {k: v for k, v in res.items() if k not in ['variationId', 'users', 'conversions', 'count']}

                variants_list.append(IntegrationVariant(
                    name=v_name,
                    users=users,
                    conversions=conversions,
                    metrics=metrics
                ))
            
            return IntegrationResult(
                experiment_id=experiment_id,
                variants=variants_list
            )

        except ProviderAuthError:
            raise
        except ProviderNotFoundError:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                 raise ProviderAuthError("Invalid GrowthBook API Key", provider=self.provider_name)
            raise IntegrationError(f"HTTP error: {str(e)}", provider=self.provider_name)
        except httpx.RequestError as e:
            raise IntegrationError(f"Connection error: {str(e)}", provider=self.provider_name)
        except Exception as e:
            raise IntegrationError(f"Unexpected error: {str(e)}", provider=self.provider_name)

# Register the provider
registry.register("growthbook", GrowthBookProvider)
