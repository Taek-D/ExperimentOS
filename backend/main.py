from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
import json
import sys
import os
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


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


def sanitize(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    return json.loads(json.dumps(obj, cls=NumpyEncoder))

# Add src to sys.path to import existing logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.experimentos.healthcheck import run_health_check
from src.experimentos.analysis import (
    calculate_primary, 
    calculate_guardrails,
    calculate_continuous_metrics,
    calculate_bayesian_insights
)
from src.experimentos.memo import generate_memo, export_html, make_decision
# Import integrations to register providers
import src.experimentos.integrations.statsig
import src.experimentos.integrations.growthbook
import src.experimentos.integrations.hackle
from backend.routers import integrations

app = FastAPI(title="ExperimentOS API")

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
async def api_analyze(file: UploadFile = File(...), guardrails: Optional[str] = None):
    # guardrails: comma separated list of columns, or None for auto-detect
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # 1. Primary Analysis
        primary_result = calculate_primary(df)
        
        # 2. Guardrails Analysis
        guardrail_cols = guardrails.split(",") if guardrails else None
        guardrail_results = calculate_guardrails(df, guardrail_columns=guardrail_cols)
        
        return sanitize({
            "status": "success",
            "primary_result": primary_result,
            "guardrail_results": guardrail_results
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
        
        continuous_results = calculate_continuous_metrics(df)
        
        return sanitize({
            "status": "success",
            "continuous_results": continuous_results
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
        
        # Get continuous results first for Bayesian continuous analysis
        continuous_results = calculate_continuous_metrics(df)
        bayesian_insights = calculate_bayesian_insights(df, continuous_results)
        
        return sanitize({
            "status": "success",
            "bayesian_insights": bayesian_insights
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DecisionMemoRequest(BaseModel):
    experiment_name: str
    health_result: Dict[str, Any]
    primary_result: Dict[str, Any]
    guardrail_results: List[Dict[str, Any]]
    bayesian_insights: Optional[Dict[str, Any]] = None


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
