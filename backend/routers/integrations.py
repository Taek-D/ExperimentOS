from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query
from typing import List, Optional, Any
import pandas as pd
from pydantic import BaseModel

from src.experimentos.integrations.registry import registry
from src.experimentos.integrations.base import IntegrationError, ProviderNotFoundError, ProviderAuthError
from src.experimentos.integrations.transform import to_experiment_df
from src.experimentos.analysis import (
    calculate_primary,
    calculate_guardrails,
    analyze_multivariant,
    calculate_guardrails_multivariant,
)
from src.experimentos.config import MULTIPLE_TESTING_METHOD
from backend.utils import sanitize

router = APIRouter(
    prefix="/api/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)

# Request-scoped API Key dependency
def get_api_key(x_integration_api_key: Optional[str] = Header(None, description="API Key for the provider")):
    if not x_integration_api_key:
        raise HTTPException(status_code=401, detail="X-Integration-Api-Key header is required")
    return x_integration_api_key

class ExperimentResponse(BaseModel):
    id: str
    name: str
    status: str
    provider: str

class AnalysisResponse(BaseModel):
    status: str
    experiment_id: str
    provider: str
    is_multivariant: Optional[bool] = None
    variant_count: Optional[int] = None
    primary_result: Any
    guardrail_results: Any = None


def _is_multivariant(df: pd.DataFrame) -> bool:
    """Auto-detect whether experiment data should use multi-variant analysis path."""
    variants = df["variant"].unique()
    return len(variants) > 2 or "treatment" not in variants

@router.get("/{provider}/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    provider: str = Path(..., description="Provider name (e.g., statsig, dummy)"),
    api_key: str = Depends(get_api_key)
):
    """
    List experiments from the specified provider.
    """
    try:
        # Get provider instance (request-scoped)
        integration = registry.get_provider(provider, api_key)
        experiments = integration.list_experiments()
        
        # Add provider name to response if missing
        for exp in experiments:
            exp.provider = provider
            
        return experiments
        
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProviderAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except IntegrationError as e:
        # Generic integration error
        raise HTTPException(status_code=502, detail=f"Integration Error: {str(e)}")
    except Exception as e:
        # Unhandled internal error
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{provider}/experiments/{experiment_id}/analyze", response_model=AnalysisResponse)
async def analyze_experiment(
    provider: str = Path(..., description="Provider name"),
    experiment_id: str = Path(..., description="Experiment ID"),
    guardrails: Optional[str] = Query(None, description="Comma-separated list of guardrail metrics"),
    api_key: str = Depends(get_api_key)
):
    """
    Fetch experiment data from provider and run analysis.
    """
    try:
        integration = registry.get_provider(provider, api_key)
        
        # 1. Fetch data
        result = integration.fetch_experiment(experiment_id)
        
        # 2. Transform to DataFrame
        df = to_experiment_df(result)
        
        # 3. Analyze
        # If no explicit guardrails asked, auto-detect all extra metric columns.
        guardrail_cols = [c.strip() for c in guardrails.split(",")] if guardrails else None
        guardrail_cols = [c for c in guardrail_cols or [] if c]
        extra_cols = [c for c in df.columns if c not in ["variant", "users", "conversions"]]
        if not guardrail_cols and extra_cols:
            guardrail_cols = extra_cols

        is_multi = _is_multivariant(df)
        if is_multi:
            primary_result = analyze_multivariant(df, MULTIPLE_TESTING_METHOD)
            primary_result["is_multivariant"] = True

            best_variant = None
            best_lift = -float("inf")
            for v_name, v_data in primary_result.get("variants", {}).items():
                if v_data.get("is_significant_corrected") and v_data["absolute_lift"] > best_lift:
                    best_lift = v_data["absolute_lift"]
                    best_variant = v_name
            primary_result["best_variant"] = best_variant

            guardrail_results = calculate_guardrails_multivariant(
                df,
                guardrail_columns=guardrail_cols or None,
            )
        else:
            primary_result = calculate_primary(df)
            guardrail_results = calculate_guardrails(
                df,
                guardrail_columns=guardrail_cols or None,
            )
        
        # Sanitize for JSON response (numpy types)
        return sanitize({
            "status": "success",
            "experiment_id": experiment_id,
            "provider": provider,
            "is_multivariant": is_multi,
            "variant_count": len(df["variant"].unique()),
            "primary_result": primary_result,
            "guardrail_results": guardrail_results
        })

    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProviderAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except IntegrationError as e:
        raise HTTPException(status_code=502, detail=f"Integration Error: {str(e)}")
    except Exception as e:
        # Log the full error in a real app
        print(f"Error analyzing experiment: {e}") 
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
