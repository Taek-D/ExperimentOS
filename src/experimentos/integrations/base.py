from typing import List, Protocol, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import abc

from .schema import IntegrationResult

@dataclass
class ExperimentSummary:
    """Summary of an experiment for listing purposes."""
    id: str
    name: str
    status: str  # e.g., 'running', 'stopped'
    last_updated: Optional[datetime] = None
    provider: str = "" # populated by the service wrapper

class IntegrationError(Exception):
    """Base exception for all integration errors."""
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.provider = provider
        self.details = details or {}

class ProviderAuthError(IntegrationError):
    """Authentication failed (invalid API key)."""
    pass

class ProviderRateLimitError(IntegrationError):
    """Rate limit exceeded."""
    pass

class ProviderNotFoundError(IntegrationError):
    """Experiment or resource not found."""
    pass

@dataclass
class RetryPolicy:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 2.0
    backoff_factor: float = 2.0

class IntegrationProvider(Protocol):
    """
    Protocol that all integration providers must implement.
    Instances are expected to be short-lived (request-scoped) and initialized with auth credentials.
    """
    
    @abc.abstractmethod
    def list_experiments(self) -> List[ExperimentSummary]:
        """List all available experiments from the provider."""
        raise NotImplementedError

    @abc.abstractmethod
    def fetch_experiment(self, experiment_id: str) -> IntegrationResult:
        """Fetch detailed results for a specific experiment."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier of the provider (e.g., 'statsig')."""
        raise NotImplementedError
