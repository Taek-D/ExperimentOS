"""
Guardrail Analysis Edge Case Tests
"""

import pytest
import pandas as pd
from src.experimentos.analysis import calculate_guardrails


def test_guardrail_threshold_boundary_worsened():
    """Guardrail delta exactly at worsened threshold should be worsened."""
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "conversions": [1000, 1100],
        "guardrail_error": [10, 20]  # delta = (20/10000) - (10/10000) = 0.001 exactly
    })
    
    result = calculate_guardrails(df, abs_threshold=0.001)
    
    assert len(result) == 1
    assert result[0]["name"] == "guardrail_error"
    assert result[0]["delta"] == 0.001
    assert result[0]["worsened"] is True  # Should be True with ">="


def test_guardrail_threshold_boundary_severe():
    """Guardrail delta exactly at severe threshold should be severe."""
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "conversions": [1000, 1100],
        "guardrail_crash": [10, 40]  # delta = (40/10000) - (10/10000) = 0.003 exactly
    })
    
    result = calculate_guardrails(df, abs_threshold=0.001, severe_threshold=0.003)
    
    assert len(result) == 1
    assert result[0]["delta"] == 0.003
    assert result[0]["worsened"] is True
    assert result[0]["severe"] is True  # Should be True with ">="


def test_guardrail_just_below_threshold():
    """Guardrail delta just below threshold should not be worsened."""
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "conversions": [1000, 1100],
        "guardrail_error": [10, 19]  # delta = 0.0009 (just below 0.001)
    })
    
    result = calculate_guardrails(df, abs_threshold=0.001)
    
    assert len(result) == 1
    assert result[0]["delta"] < 0.001
    assert result[0]["worsened"] is False


def test_guardrail_negative_delta():
    """Guardrail with negative delta (improvement) should not be worsened."""
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "conversions": [1000, 1100],
        "guardrail_error": [20, 10]  # delta = -0.001 (improvement)
    })
    
    result = calculate_guardrails(df, abs_threshold=0.001)
    
    assert len(result) == 1
    assert result[0]["delta"] == -0.001
    assert result[0]["worsened"] is False  # Negative delta is not worsened


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
