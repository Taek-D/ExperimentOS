import pytest
from src.experimentos.memo import make_decision, generate_memo


HEALTHY_HEALTH = {
    "overall_status": "Healthy",
    "schema": {"status": "Healthy", "issues": []},
    "srm": {"status": "Healthy", "message": "No SRM", "p_value": 0.999},
}


def _mv_primary(overall_sig=True, overall_p=0.001, variants=None):
    """Helper to build a multi-variant primary result."""
    if variants is None:
        variants = {
            "variant_a": {
                "users": 1000,
                "conversions": 120,
                "rate": 0.12,
                "absolute_lift": 0.02,
                "relative_lift": 0.2,
                "ci_95": [0.005, 0.035],
                "p_value": 0.03,
                "p_value_corrected": 0.06,
                "is_significant": True,
                "is_significant_corrected": False,
            },
            "variant_b": {
                "users": 1000,
                "conversions": 150,
                "rate": 0.15,
                "absolute_lift": 0.05,
                "relative_lift": 0.5,
                "ci_95": [0.025, 0.075],
                "p_value": 0.001,
                "p_value_corrected": 0.002,
                "is_significant": True,
                "is_significant_corrected": True,
            },
        }
    return {
        "is_multivariant": True,
        "overall": {
            "chi2_stat": 15.0,
            "p_value": overall_p,
            "dof": 2,
            "is_significant": overall_sig,
        },
        "control_stats": {"users": 1000, "conversions": 100, "rate": 0.10},
        "variants": variants,
        "correction_method": "bonferroni",
        "best_variant": "variant_b",
        "all_pairs": [],
    }


def _mv_guardrails(by_variant=None, any_severe=False, any_worsened=False):
    """Helper to build multi-variant guardrail results."""
    if by_variant is None:
        by_variant = {
            "variant_a": [
                {
                    "name": "error_count", "variant": "variant_a",
                    "control_count": 50, "treatment_count": 48,
                    "control_rate": 0.005, "treatment_rate": 0.0048,
                    "delta": -0.0002, "relative_lift": -0.04,
                    "severe": False, "worsened": False, "p_value": 0.87,
                }
            ],
            "variant_b": [
                {
                    "name": "error_count", "variant": "variant_b",
                    "control_count": 50, "treatment_count": 49,
                    "control_rate": 0.005, "treatment_rate": 0.0049,
                    "delta": -0.0001, "relative_lift": -0.02,
                    "severe": False, "worsened": False, "p_value": 0.93,
                }
            ],
        }
    return {
        "by_variant": by_variant,
        "any_severe": any_severe,
        "any_worsened": any_worsened,
        "summary": [],
    }


class TestMultivariantDecision:
    """Multi-variant decision rule tests."""

    def test_rule1_overall_not_significant(self):
        """Overall chi-square not significant → Hold."""
        primary = _mv_primary(overall_sig=False, overall_p=0.45)
        result = make_decision(HEALTHY_HEALTH, primary, _mv_guardrails())

        assert result["decision"] == "Hold"
        assert "비유의" in result["reason"]
        assert result["best_variant"] is None

    def test_rule2_severe_guardrail_rollback(self):
        """Best variant significant + severe guardrail → Rollback."""
        primary = _mv_primary()
        guardrails = _mv_guardrails(
            by_variant={
                "variant_a": [{"name": "error_count", "delta": 0.0, "severe": False, "worsened": False}],
                "variant_b": [{"name": "error_count", "delta": 0.005, "severe": True, "worsened": True}],
            },
            any_severe=True,
        )
        result = make_decision(HEALTHY_HEALTH, primary, guardrails)

        assert result["decision"] == "Rollback"
        assert result["best_variant"] == "variant_b"
        assert "심각한 Guardrail" in result["reason"]

    def test_rule3_worsened_guardrail_hold(self):
        """Best variant significant + worsened (non-severe) guardrail → Hold."""
        primary = _mv_primary()
        guardrails = _mv_guardrails(
            by_variant={
                "variant_a": [{"name": "error_count", "delta": 0.0, "severe": False, "worsened": False}],
                "variant_b": [{"name": "error_count", "delta": 0.002, "severe": False, "worsened": True}],
            },
            any_worsened=True,
        )
        result = make_decision(HEALTHY_HEALTH, primary, guardrails)

        assert result["decision"] == "Hold"
        assert result["best_variant"] == "variant_b"
        assert "Guardrail 악화" in result["reason"]

    def test_rule4_launch_best_variant(self):
        """Best variant significant + guardrails OK → Launch."""
        primary = _mv_primary()
        result = make_decision(HEALTHY_HEALTH, primary, _mv_guardrails())

        assert result["decision"] == "Launch"
        assert result["best_variant"] == "variant_b"
        assert "variant_b" in result["reason"]

    def test_rule5_no_individual_significant(self):
        """Overall significant but no individual variant significant after correction → Hold."""
        variants = {
            "variant_a": {
                "users": 1000, "conversions": 110, "rate": 0.11,
                "absolute_lift": 0.01, "relative_lift": 0.1,
                "ci_95": [-0.005, 0.025], "p_value": 0.08,
                "p_value_corrected": 0.16,
                "is_significant": False, "is_significant_corrected": False,
            },
            "variant_b": {
                "users": 1000, "conversions": 115, "rate": 0.115,
                "absolute_lift": 0.015, "relative_lift": 0.15,
                "ci_95": [-0.001, 0.031], "p_value": 0.06,
                "p_value_corrected": 0.12,
                "is_significant": False, "is_significant_corrected": False,
            },
        }
        primary = _mv_primary(overall_sig=True, overall_p=0.04, variants=variants)
        result = make_decision(HEALTHY_HEALTH, primary, _mv_guardrails())

        assert result["decision"] == "Hold"
        assert "보정 후 모두 비유의" in result["reason"]

    def test_health_blocked_overrides_multivariant(self):
        """Blocked health still overrides multi-variant decision."""
        blocked_health = {
            "overall_status": "Blocked",
            "schema": {"status": "Blocked", "issues": ["Missing column: users"]},
        }
        primary = _mv_primary()
        result = make_decision(blocked_health, primary, _mv_guardrails())

        assert result["decision"] == "Hold"
        assert "Blocked" in result["reason"]


class TestMultivariantMemo:
    """Tests for generate_memo with multi-variant data."""

    def test_generates_multivariant_memo(self):
        """generate_memo() produces valid markdown for multi-variant."""
        primary = _mv_primary()
        decision = make_decision(HEALTHY_HEALTH, primary, _mv_guardrails())
        memo = generate_memo(
            experiment_name="Test Multi-Variant",
            decision=decision,
            health=HEALTHY_HEALTH,
            primary=primary,
            guardrails=_mv_guardrails(),
        )

        assert "Multi-Variant" in memo
        assert "variant_a" in memo
        assert "variant_b" in memo
        assert "Overall Test" in memo
        assert "Per-Variant Comparisons" in memo
