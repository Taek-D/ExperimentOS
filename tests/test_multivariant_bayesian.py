import pytest
import pandas as pd
from src.experimentos.bayesian import calculate_beta_binomial_multivariant
from src.experimentos.analysis import calculate_bayesian_insights_multivariant


class TestBetaBinomialMultivariant:
    """Tests for calculate_beta_binomial_multivariant()."""

    def test_basic_3_variant(self):
        """3 variants: control vs two treatments."""
        result = calculate_beta_binomial_multivariant(
            control_conversions=100,
            control_total=1000,
            treatments=[
                {"name": "variant_a", "conversions": 120, "total": 1000},
                {"name": "variant_b", "conversions": 130, "total": 1000},
            ],
        )

        # vs_control
        assert "variant_a" in result["vs_control"]
        assert "variant_b" in result["vs_control"]
        assert 0 < result["vs_control"]["variant_a"]["prob_beats_control"] < 1
        assert 0 < result["vs_control"]["variant_b"]["prob_beats_control"] < 1

        # variant_b should beat control more often than variant_a
        assert (
            result["vs_control"]["variant_b"]["prob_beats_control"]
            > result["vs_control"]["variant_a"]["prob_beats_control"]
        )

        # prob_being_best
        assert "control" in result["prob_being_best"]
        assert "variant_a" in result["prob_being_best"]
        assert "variant_b" in result["prob_being_best"]

        # Sum of prob_being_best should be ~1.0
        total = sum(result["prob_being_best"].values())
        assert total == pytest.approx(1.0, abs=0.01)

        # variant_b is the best most often (13% vs 12% vs 10%)
        assert result["prob_being_best"]["variant_b"] > result["prob_being_best"]["control"]

    def test_identical_variants(self):
        """All variants have same rate -> roughly equal prob_being_best."""
        result = calculate_beta_binomial_multivariant(
            control_conversions=100,
            control_total=1000,
            treatments=[
                {"name": "variant_a", "conversions": 100, "total": 1000},
                {"name": "variant_b", "conversions": 100, "total": 1000},
            ],
        )

        # Each should have ~33% chance of being best
        for name in ["control", "variant_a", "variant_b"]:
            assert result["prob_being_best"][name] == pytest.approx(1 / 3, abs=0.05)

    def test_single_treatment(self):
        """Single treatment degenerates to standard case."""
        result = calculate_beta_binomial_multivariant(
            control_conversions=100,
            control_total=1000,
            treatments=[{"name": "treatment", "conversions": 150, "total": 1000}],
        )

        assert "treatment" in result["vs_control"]
        assert result["vs_control"]["treatment"]["prob_beats_control"] > 0.9

        total = sum(result["prob_being_best"].values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_posterior_returned(self):
        """Posterior parameters returned for each treatment."""
        result = calculate_beta_binomial_multivariant(
            control_conversions=100,
            control_total=1000,
            treatments=[{"name": "variant_a", "conversions": 120, "total": 1000}],
        )

        assert result["control_posterior"]["alpha"] == 101
        assert result["control_posterior"]["beta"] == 901
        assert result["vs_control"]["variant_a"]["posterior"]["alpha"] == 121
        assert result["vs_control"]["variant_a"]["posterior"]["beta"] == 881

    def test_expected_loss(self):
        """Expected loss is non-negative."""
        result = calculate_beta_binomial_multivariant(
            control_conversions=100,
            control_total=1000,
            treatments=[
                {"name": "variant_a", "conversions": 120, "total": 1000},
                {"name": "variant_b", "conversions": 80, "total": 1000},
            ],
        )

        for v in result["vs_control"].values():
            assert v["expected_loss"] >= 0


class TestBayesianInsightsMultivariant:
    """Tests for calculate_bayesian_insights_multivariant() orchestrator."""

    def test_basic_conversion(self):
        """Test conversion insights with 3 variants."""
        df = pd.DataFrame({
            "variant": ["control", "variant_a", "variant_b"],
            "users": [1000, 1000, 1000],
            "conversions": [100, 120, 130],
        })
        result = calculate_bayesian_insights_multivariant(df)

        assert result["conversion"] is not None
        assert "vs_control" in result["conversion"]
        assert "prob_being_best" in result["conversion"]

    def test_no_control(self):
        """No control variant returns empty insights."""
        df = pd.DataFrame({
            "variant": ["variant_a", "variant_b"],
            "users": [1000, 1000],
            "conversions": [100, 120],
        })
        result = calculate_bayesian_insights_multivariant(df)

        assert result["conversion"] is None
