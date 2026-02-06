import pytest
import pandas as pd
import numpy as np
from src.experimentos.analysis import analyze_multivariant

def test_analyze_multivariant_3_variants():
    """Test standard 3-variant case (Control, A, B)."""
    # Control: 1000/100 (10%)
    # A: 1000/120 (12%)
    # B: 1000/130 (13%)
    data = {
        "variant": ["control", "variant_a", "variant_b"],
        "users": [1000, 1000, 1000],
        "conversions": [100, 120, 130]
    }
    df = pd.DataFrame(data)
    
    result = analyze_multivariant(df)
    
    # 1. Overall stats
    overall = result.get("overall", {})
    assert "p_value" in overall
    assert overall["chi2_stat"] > 0
    # Independence should be rejected or close to it (10% vs 12% vs 13% might be significant)
    
    # 2. Pairwise A vs Control
    res_a = result["variants"]["variant_a"]
    assert res_a["rate"] == 0.12
    assert res_a["absolute_lift"] == pytest.approx(0.02)
    assert res_a["relative_lift"] == pytest.approx(0.2, 0.01)
    
    # 3. Pairwise B vs Control
    res_b = result["variants"]["variant_b"]
    assert res_b["rate"] == 0.13
    assert res_b["absolute_lift"] == pytest.approx(0.03)
    assert res_b["relative_lift"] == pytest.approx(0.3, 0.01)

    # 4. Control stats present
    assert result["control_stats"]["rate"] == 0.10

def test_analyze_multivariant_no_control():
    """Test behavior when control is missing."""
    data = {
        "variant": ["A", "B"],
        "users": [100, 100],
        "conversions": [10, 10]
    }
    df = pd.DataFrame(data)
    
    result = analyze_multivariant(df)
    
    # Overall might still run
    assert "p_value" in result["overall"]
    
    # Variants dict should generally be empty or reflect logic (skipped pairwise)
    assert result["variants"] == {}

def test_analyze_multivariant_zero_users():
    """Test edge case with zero users."""
    data = {
        "variant": ["control", "test"],
        "users": [0, 0],
        "conversions": [0, 0]
    }
    df = pd.DataFrame(data)
    
    result = analyze_multivariant(df)
    
    # Chi2 should handle zeros or exception caught
    if "error" not in result["overall"]:
        assert result["overall"]["p_value"] == 1.0 or pd.isna(result["overall"]["p_value"])
        
    # Pairwise should be safe
    res_test = result["variants"]["test"]
    assert res_test["rate"] == 0.0
    assert res_test["p_value"] == 1.0

def test_analyze_multivariant_matches_2_variant():
    """Ensure consistency with 2-variant case (logic check)."""
    # Control: 1000/100, Test: 1000/120
    data = {
        "variant": ["control", "test"],
        "users": [1000, 1000],
        "conversions": [100, 120]
    }
    df = pd.DataFrame(data)
    
    result = analyze_multivariant(df)
    res_test = result["variants"]["test"]
    
    # Hand calc or approx
    # 12% vs 10%
    assert res_test["absolute_lift"] == pytest.approx(0.02)
    assert res_test["p_value"] < 0.2 # Rough check
