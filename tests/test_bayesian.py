import pytest
from src.experimentos.bayesian import calculate_beta_binomial, calculate_continuous_bayes

class TestBayesianAnalysis:
    
    @pytest.mark.parametrize("c_conv, c_total, t_conv, t_total, expected_prob_range", [
        (100, 1000, 120, 1000, (0.8, 1.0)),   # Treatment better (12% vs 10%)
        (100, 1000, 100, 1000, (0.4, 0.6)),   # Equal (approx 50%)
        (120, 1000, 100, 1000, (0.0, 0.2)),   # Control better
    ])
    def test_beta_binomial_smoke(self, c_conv, c_total, t_conv, t_total, expected_prob_range):
        """Smoke test for Beta-Binomial probability ranges"""
        res = calculate_beta_binomial(c_conv, c_total, t_conv, t_total)
        prob = res["prob_treatment_beats_control"]
        assert expected_prob_range[0] <= prob <= expected_prob_range[1]

    def test_beta_binomial_deterministic(self):
        """Ensure results are repeatable with fixed seed"""
        res1 = calculate_beta_binomial(100, 1000, 120, 1000)
        res2 = calculate_beta_binomial(100, 1000, 120, 1000)
        
        # Exact float equality because we reset RNG seed every call
        assert res1["prob_treatment_beats_control"] == res2["prob_treatment_beats_control"]

    def test_continuous_bayes_deterministic(self):
        """Ensure continuous simulation is repeatable"""
        # Scenario: Treatment better mean (11 vs 10)
        c_stats = {"sum": 1000, "sum_sq": 10400, "n": 100} # mean 10, var 4
        t_stats = {"sum": 1100, "sum_sq": 12500, "n": 100} # mean 11, var 5
        
        res1 = calculate_continuous_bayes(c_stats, t_stats)
        res2 = calculate_continuous_bayes(c_stats, t_stats)
        
        assert res1["prob_treatment_beats_control"] == res2["prob_treatment_beats_control"]
        assert res1["prob_treatment_beats_control"] > 0.95
