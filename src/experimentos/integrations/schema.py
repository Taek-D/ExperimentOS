from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo

class IntegrationVariant(BaseModel):
    """
    Represents a single variant in an experiment from an external integration.
    """
    name: str = Field(..., description="Name of the variant (e.g., 'control', 'treatment')")
    users: int = Field(..., ge=0, description="Total number of users exposed to this variant")
    conversions: int = Field(..., ge=0, description="Number of users who converted")
    metrics: dict[str, float] | None = Field(default_factory=dict, description="Additional metrics (guardrails, continuous)")

    @model_validator(mode='after')
    def validate_conversions_le_users(self) -> 'IntegrationVariant':
        if self.conversions > self.users:
            raise ValueError('conversions cannot be greater than users')
        return self

class IntegrationResult(BaseModel):
    """
    Standardized result object from an external integration API.
    """
    experiment_id: str = Field(..., description="Unique identifier for the experiment")
    variants: list[IntegrationVariant] = Field(..., min_length=2, description="List of variants (must have at least 2)")
    
    @field_validator('variants')
    @classmethod
    def validate_variants_names(cls, v: list[IntegrationVariant], info: ValidationInfo) -> list[IntegrationVariant]:
        """Ensure variant names are unique."""
        names = [variant.name for variant in v]
        if len(names) != len(set(names)):
            raise ValueError('Variant names must be unique')
        return v
