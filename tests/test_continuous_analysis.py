import pytest
import numpy as np
from src.experimentos.continuous_analysis import calculate_continuous_lift

class TestContinuousAnalysis:
    
    @pytest.fixture
    def basic_stats(self):
        """Fixture for basic valid stats"""
        # Control: mean=10, var=4, n=100
        n_c = 100
        mean_c = 10.0
        var_c = 4.0
        sum_c = mean_c * n_c
        sum_sq_c = var_c * (n_c - 1) + (sum_c**2 / n_c)
        
        # Treatment: mean=11, var=5, n=100
        n_t = 100
        mean_t = 11.0
        var_t = 5.0
        sum_t = mean_t * n_t
        sum_sq_t = var_t * (n_t - 1) + (sum_t**2 / n_t)
        
        return {
            "control": {"sum": sum_c, "sum_sq": sum_sq_c, "n": n_c},
            "treatment": {"sum": sum_t, "sum_sq": sum_sq_t, "n": n_t}
        }

    def test_welch_t_test_valid(self, basic_stats):
        """Standard valid case: Distinct means, sufficient N"""
        result = calculate_continuous_lift(basic_stats["control"], basic_stats["treatment"], "test_metric")
        
        assert result["is_valid"] is True
        assert result["control_mean"] == 10.0
        assert result["treatment_mean"] == 11.0
        assert result["absolute_lift"] == 1.0
        assert result["relative_lift"] == pytest.approx(0.1)
        assert result["is_significant"]
        assert result["p_value"] < 0.01

    @pytest.mark.parametrize("n_c, n_t, expected_valid", [
        (1, 100, False),  # Control insufficient
        (100, 1, False),  # Treatment insufficient
        (1, 1, False),    # Both insufficient
        (2, 2, True),     # Minimal sufficient
    ])
    def test_insufficient_data_parametrized(self, n_c, n_t, expected_valid):
        """Parametrized test for insufficient data edge cases"""
        c_stats = {"sum": 10, "sum_sq": 100, "n": n_c}
        t_stats = {"sum": 10, "sum_sq": 100, "n": n_t}
        
        result = calculate_continuous_lift(c_stats, t_stats, "test_metric")
        assert result["is_valid"] is expected_valid
        if not expected_valid:
            assert "Insufficient data" in result["error"]

    def test_zero_variance(self):
        """Identical constant values (variance 0)"""
        n = 100
        s = 1000.0
        ss = 10000.0 # sum^2/n exactly
        
        c_stats = {"sum": s, "sum_sq": ss, "n": n}
        t_stats = {"sum": s, "sum_sq": ss, "n": n}
        
        result = calculate_continuous_lift(c_stats, t_stats, "test_metric")
        assert result["is_valid"] is True
        assert result["p_value"] == 1.0
        assert result["absolute_lift"] == 0.0

    def test_large_numbers_numerical_stability(self):
        """Test with large numbers to ensure no overflow/underflow issues"""
        # Scenario: Revenue in millions
        n = 10000
        mean = 1000000.0
        var = 10000.0
        
        sum_val = mean * n
        sum_sq = var * (n - 1) + (sum_val**2 / n)
        
        stats = {"sum": sum_val, "sum_sq": sum_sq, "n": n}
        
        # Identical control and treatment
        result = calculate_continuous_lift(stats, stats, "revenue_metric")
        
        assert result["is_valid"] is True
        assert result["control_mean"] == pytest.approx(1000000.0)
        assert result["p_value"] > 0.99 # Should be effectively 1.0
