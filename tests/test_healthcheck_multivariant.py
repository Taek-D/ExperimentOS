import pytest
import pandas as pd
from src.experimentos.healthcheck import run_health_check, validate_schema

def test_healthcheck_3_variants_healthy():
    """Test with 3 variants equally split (Healthy)"""
    data = {
        "variant": ["control", "variant_b", "variant_c"],
        "users": [1000, 1005, 995],
        "conversions": [100, 105, 95]
    }
    df = pd.DataFrame(data)
    
    result = run_health_check(df)
    
    assert result["overall_status"] == "Healthy"
    assert result["schema"]["status"] == "Healthy"
    assert result["srm"]["status"] == "Healthy"
    # Check if 'variant_c' is in observed
    assert "variant_c" in result["srm"]["observed"]

def test_healthcheck_3_variants_srm_blocked():
    """Test with 3 variants with severe imbalance (SRM Blocked)"""
    data = {
        "variant": ["control", "variant_b", "variant_c"],
        "users": [10000, 5000, 10000], # One group significantly smaller
        "conversions": [1000, 500, 1000]
    }
    df = pd.DataFrame(data)
    
    result = run_health_check(df)
    
    assert result["overall_status"] == "Blocked"
    assert result["srm"]["status"] == "Blocked"
    assert "SRM" in result["srm"]["message"]

def test_healthcheck_missing_control_multivariant():
    """Test with 3 variants but missing 'control' (Blocked by Schema)"""
    data = {
        "variant": ["A", "B", "C"],
        "users": [1000, 1000, 1000],
        "conversions": [100, 100, 100]
    }
    df = pd.DataFrame(data)
    
    result = validate_schema(df)
    
    assert result["status"] == "Blocked"
    assert "control" in result["issues"][0]

def test_healthcheck_custom_split():
    """Test with 3 variants and custom expected split (50/25/25)"""
    # Expected: 2000, 1000, 1000
    data = {
        "variant": ["control", "b", "c"],
        "users": [2000, 1000, 1000],
        "conversions": [200, 100, 100]
    }
    df = pd.DataFrame(data)
    
    # We pass expected split as list.
    # Logic in run_health_check assumes order matches DF row order.
    # run_health_check(df, expected_split=[50, 25, 25])
    
    result = run_health_check(df, expected_split=[50, 25, 25])
    
    assert result["overall_status"] == "Healthy"
    assert result["srm"]["status"] == "Healthy"
    assert result["srm"]["expected"]["control"] == 2000.0

def test_healthcheck_backward_compatibility_2_variants():
    """Ensure existing 2-variant logic still works"""
    data = {
        "variant": ["control", "treatment"],
        "users": [1000, 1000],
        "conversions": [100, 110]
    }
    df = pd.DataFrame(data)
    
    result = run_health_check(df)
    
    assert result["overall_status"] == "Healthy"
    assert result["srm"]["status"] == "Healthy"
    assert result["srm"]["observed"]["control"] == 1000
    assert result["srm"]["observed"]["treatment"] == 1000
