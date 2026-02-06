from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query
from typing import List, Optional, Any
from pydantic import BaseModel

from src.experimentos.integrations.registry import registry
from src.experimentos.integrations.base import IntegrationError, ProviderNotFoundError, ProviderAuthError
from src.experimentos.integrations.transform import to_experiment_df
from src.experimentos.analysis import calculate_primary, calculate_guardrails
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
    primary_result: Any
    guardrail_results: Optional[List[Any]] = None

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
        # Run Primary Analysis
        primary_result = calculate_primary(df)
        
        # Run Guardrails Analysis if requested or if metrics exist
        # transform.py adds metrics as columns. We can auto-detect or use user input.
        # If user input provided, use that. Else, maybe use all other columns?
        # For now, let's stick to explicit user request via query param or default to None.
        guardrail_cols = guardrails.split(",") if guardrails else None
        
        # If no explicit guardrails asked, but we have metrics in DF (excluding standard ones),
        # we could potentially auto-detect. 
        # Standard cols: variant, users, conversions.
        extra_cols = [c for c in df.columns if c not in ['variant', 'users', 'conversions']]
        if not guardrail_cols and extra_cols:
             guardrail_cols = extra_cols

        guardrail_results = calculate_guardrails(df, guardrail_columns=guardrail_cols)
        
        # Sanitize for JSON response (numpy types)
        return sanitize({
            "status": "success",
            "experiment_id": experiment_id,
            "provider": provider,
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
