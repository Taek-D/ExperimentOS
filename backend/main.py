from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
import json
import sys
import os
from pydantic import BaseModel
from typing import Any


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class SafeJSONResponse(JSONResponse):
    """JSONResponse that safely handles NaN/Inf and numpy types.

    Two-pass approach:
      1) json.dumps with allow_nan=True + NumpyEncoder -> produces string with NaN tokens
      2) json.loads with parse_constant -> converts NaN/Infinity to None
      3) json.dumps again -> clean, RFC-compliant JSON
    """

    def render(self, content: Any) -> bytes:
        text = json.dumps(
            content, cls=NumpyEncoder, allow_nan=True,
            ensure_ascii=False, separators=(",", ":"),
        )
        clean = json.loads(text, parse_constant=lambda _: None)
        return json.dumps(
            clean, ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")


def sanitize(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    text = json.dumps(obj, cls=NumpyEncoder, allow_nan=True)
    return json.loads(text, parse_constant=lambda _: None)

# Add src to sys.path to import existing logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.experimentos.healthcheck import run_health_check
from src.experimentos.analysis import (
    calculate_primary,
    calculate_guardrails,
    calculate_continuous_metrics,
    calculate_bayesian_insights,
    analyze_multivariant,
    calculate_guardrails_multivariant,
    calculate_continuous_metrics_multivariant,
    calculate_bayesian_insights_multivariant,
)
from src.experimentos.config import MULTIPLE_TESTING_METHOD
from src.experimentos.memo import generate_memo, export_html, make_decision
from src.experimentos.sequential import analyze_sequential, calculate_boundaries
# Import integrations to register providers
import src.experimentos.integrations.statsig
import src.experimentos.integrations.growthbook
import src.experimentos.integrations.hackle
from backend.routers import integrations

app = FastAPI(title="ExperimentOS API", default_response_class=SafeJSONResponse)


def _is_multivariant(df: pd.DataFrame) -> bool:
    """Auto-detect whether the experiment is multi-variant (3+ variants or non-standard names)."""
    variants = df["variant"].unique()
    return len(variants) > 2 or "treatment" not in variants

# Register Integration Router
app.include_router(integrations.router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ExperimentOS API is running"}

@app.post("/api/health-check")
async def api_health_check(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Run existing health check logic
        result = run_health_check(df)
        
        # return basic stats for preview
        preview = df.head().fillna("").to_dict(orient="records")
        columns = list(df.columns)
        
        return {
            "status": "success",
            "result": result,
            "preview": preview,
            "columns": columns,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnalysisRequest(BaseModel):
    # We might need to receive the file content again or store it temporarily.
    # For a stateless MVP without DB, the React app should probably send the file content 
    # OR we handle upload and analysis in one go? 
    # Better yet: frontend performs health check, if green, user clicks "Analyze", 
    # frontend sends the file AGAIN (or the same file object).
    # Since we are modifying the architecture to be stateless, let's accept file upload for analysis too.
    pass

@app.post("/api/analyze")
async def api_analyze(file: UploadFile = File(...), guardrails: str | None = None):
    # guardrails: comma separated list of columns, or None for auto-detect
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        guardrail_cols = guardrails.split(",") if guardrails else None
        is_multi = _is_multivariant(df)

        if is_multi:
            # Multi-variant path
            primary_result = analyze_multivariant(df, MULTIPLE_TESTING_METHOD)
            primary_result["is_multivariant"] = True

            # Determine best variant
            best_variant = None
            best_lift = -float("inf")
            for v_name, v_data in primary_result.get("variants", {}).items():
                if v_data.get("is_significant_corrected") and v_data["absolute_lift"] > best_lift:
                    best_lift = v_data["absolute_lift"]
                    best_variant = v_name
            primary_result["best_variant"] = best_variant

            guardrail_results = calculate_guardrails_multivariant(
                df, guardrail_columns=guardrail_cols
            )
        else:
            # 2-variant path (기존 코드 그대로)
            primary_result = calculate_primary(df)
            guardrail_results = calculate_guardrails(df, guardrail_columns=guardrail_cols)

        return sanitize({
            "status": "success",
            "is_multivariant": is_multi,
            "variant_count": len(df["variant"].unique()),
            "primary_result": primary_result,
            "guardrail_results": guardrail_results,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/continuous-metrics")
async def api_continuous_metrics(file: UploadFile = File(...)):
    """Analyze continuous metrics using Welch's t-test"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        is_multi = _is_multivariant(df)

        if is_multi:
            continuous_results = calculate_continuous_metrics_multivariant(df)
        else:
            continuous_results = calculate_continuous_metrics(df)

        return sanitize({
            "status": "success",
            "is_multivariant": is_multi,
            "continuous_results": continuous_results,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bayesian-analysis")
async def api_bayesian_analysis(file: UploadFile = File(...)):
    """Perform Bayesian analysis (informational only)"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        is_multi = _is_multivariant(df)

        if is_multi:
            continuous_results = calculate_continuous_metrics_multivariant(df)
            bayesian_insights = calculate_bayesian_insights_multivariant(
                df, continuous_results
            )
        else:
            continuous_results = calculate_continuous_metrics(df)
            bayesian_insights = calculate_bayesian_insights(df, continuous_results)

        return sanitize({
            "status": "success",
            "is_multivariant": is_multi,
            "bayesian_insights": bayesian_insights,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DecisionMemoRequest(BaseModel):
    experiment_name: str
    health_result: dict[str, Any]
    primary_result: dict[str, Any]
    guardrail_results: Any  # list[dict] for 2-variant, dict for multi-variant
    bayesian_insights: dict[str, Any] | None = None


@app.post("/api/decision-memo")
async def api_decision_memo(request: DecisionMemoRequest):
    """Generate decision memo in Markdown and HTML formats"""
    try:
        # Make decision first
        decision_result = make_decision(
            health=request.health_result,
            primary=request.primary_result,
            guardrails=request.guardrail_results
        )
        
        # Generate memo markdown
        memo_markdown = generate_memo(
            experiment_name=request.experiment_name,
            decision=decision_result,
            health=request.health_result,
            primary=request.primary_result,
            guardrails=request.guardrail_results,
            bayesian_insights=request.bayesian_insights
        )
        
        # Export to HTML
        memo_html = export_html(memo_markdown)
        
        return {
            "status": "success",
            "decision": decision_result,
            "memo_markdown": memo_markdown,
            "memo_html": memo_html
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SequentialAnalysisRequest(BaseModel):
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int
    target_sample_size: int
    current_look: int
    max_looks: int = 5
    alpha: float = 0.05
    boundary_type: str = "obrien_fleming"
    previous_looks: list[dict[str, Any]] | None = None


@app.post("/api/sequential-analysis")
async def api_sequential_analysis(request: SequentialAnalysisRequest):
    """Run sequential analysis for early stopping decision."""
    try:
        result = analyze_sequential(
            control_users=request.control_users,
            control_conversions=request.control_conversions,
            treatment_users=request.treatment_users,
            treatment_conversions=request.treatment_conversions,
            target_sample_size=request.target_sample_size,
            current_look=request.current_look,
            max_looks=request.max_looks,
            alpha=request.alpha,
            boundary_type=request.boundary_type,
            previous_looks=request.previous_looks,
        )
        return sanitize({"status": "success", **result})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sequential-boundaries")
async def api_sequential_boundaries(
    max_looks: int = 5,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
):
    """Get boundary values for visualization/planning."""
    try:
        boundaries = calculate_boundaries(
            max_looks=max_looks,
            alpha=alpha,
            boundary_type=boundary_type,
        )
        return sanitize({
            "boundaries": boundaries,
            "config": {
                "max_looks": max_looks,
                "alpha": alpha,
                "boundary_type": boundary_type,
            },
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
