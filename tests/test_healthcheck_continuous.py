import pandas as pd
import pytest
from src.experimentos.healthcheck import run_health_check

class TestHealthCheckContinuous:
    def test_continuous_schema_missing_sum_sq(self):
        """Test that missing _sum_sq column for a _sum metric triggers Blocked status"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [1000, 1000],
            "conversions": [100, 120],
            "revenue_sum": [50000, 60000],
            # revenue_sum_sq is missing
        })
        
        result = run_health_check(df)
        assert result["overall_status"] == "Blocked"
        assert any("Continuous schema error" in i for i in result["schema"]["issues"])

    def test_continuous_schema_valid(self):
        """Test valid continuous schema"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [1000, 1000],
            "conversions": [100, 120],
            "revenue_sum": [50000, 60000],
            "revenue_sum_sq": [3000000, 4000000]
        })
        
        result = run_health_check(df)
        assert result["overall_status"] == "Healthy"

    def test_invalid_variance(self):
        """Test mathematically impossible variance (sum_sq < sum^2/n)"""
        # sum=100, n=10, sum^2/n = 10000/10 = 1000
        # sum_sq=900 (less than 1000) -> Impossible
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10, 10],
            "conversions": [1, 1],
            "revenue_sum": [100, 100],
            "revenue_sum_sq": [900, 900]
        })
        
        result = run_health_check(df)
        assert result["overall_status"] == "Blocked"
        assert any("Invalid variance" in i for i in result["schema"]["issues"])
