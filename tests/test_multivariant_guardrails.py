import pytest
import pandas as pd
from src.experimentos.analysis import calculate_guardrails_multivariant


def _make_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame(data)


class TestCalculateGuardrailsMultivariant:
    """Tests for calculate_guardrails_multivariant()."""

    def test_basic_3_variant(self):
        """3 variants, one guardrail with no worsening."""
        df = _make_df({
            "variant": ["control", "variant_a", "variant_b"],
            "users": [1000, 1000, 1000],
            "conversions": [100, 120, 130],
            "error_count": [50, 48, 52],
        })
        result = calculate_guardrails_multivariant(df)

        assert "by_variant" in result
        assert "variant_a" in result["by_variant"]
        assert "variant_b" in result["by_variant"]
        assert len(result["by_variant"]["variant_a"]) == 1
        assert result["by_variant"]["variant_a"][0]["name"] == "error_count"

    def test_severe_detection(self):
        """Severe worsening detected in one variant."""
        df = _make_df({
            "variant": ["control", "variant_a", "variant_b"],
            "users": [10000, 10000, 10000],
            "conversions": [1000, 1200, 1100],
            "error_count": [50, 50, 200],  # variant_b severe worsening
        })
        result = calculate_guardrails_multivariant(df)

        assert result["any_severe"] is True
        assert result["any_worsened"] is True

        # variant_b error_count should be severe
        vb_guardrails = result["by_variant"]["variant_b"]
        error_g = [g for g in vb_guardrails if g["name"] == "error_count"][0]
        assert error_g["severe"] is True

        # variant_a error_count should be OK
        va_guardrails = result["by_variant"]["variant_a"]
        error_g_a = [g for g in va_guardrails if g["name"] == "error_count"][0]
        assert error_g_a["severe"] is False
        assert error_g_a["worsened"] is False

    def test_no_guardrails(self):
        """No guardrail columns present."""
        df = _make_df({
            "variant": ["control", "variant_a"],
            "users": [1000, 1000],
            "conversions": [100, 120],
        })
        result = calculate_guardrails_multivariant(df)

        assert result["by_variant"] == {}
        assert result["any_severe"] is False
        assert result["any_worsened"] is False

    def test_no_control(self):
        """No control variant present."""
        df = _make_df({
            "variant": ["variant_a", "variant_b"],
            "users": [1000, 1000],
            "conversions": [100, 120],
            "error_count": [50, 60],
        })
        result = calculate_guardrails_multivariant(df)

        assert result["by_variant"] == {}
        assert result["any_severe"] is False

    def test_summary_tracks_worst(self):
        """Summary shows worst variant per guardrail."""
        df = _make_df({
            "variant": ["control", "variant_a", "variant_b"],
            "users": [10000, 10000, 10000],
            "conversions": [1000, 1200, 1100],
            "error_count": [50, 80, 200],
        })
        result = calculate_guardrails_multivariant(df)

        summary = result["summary"]
        assert len(summary) == 1
        assert summary[0]["name"] == "error_count"
        assert summary[0]["worst_variant"] == "variant_b"

    def test_explicit_guardrail_columns(self):
        """Only specified columns are used as guardrails."""
        df = _make_df({
            "variant": ["control", "variant_a"],
            "users": [1000, 1000],
            "conversions": [100, 120],
            "error_count": [50, 60],
            "bounce_count": [200, 210],
        })
        result = calculate_guardrails_multivariant(
            df, guardrail_columns=["error_count"]
        )

        va_guardrails = result["by_variant"]["variant_a"]
        assert len(va_guardrails) == 1
        assert va_guardrails[0]["name"] == "error_count"

    def test_multiple_guardrails(self):
        """Multiple guardrail columns across multiple variants."""
        df = _make_df({
            "variant": ["control", "variant_a", "variant_b", "variant_c"],
            "users": [5000, 5000, 5000, 5000],
            "conversions": [500, 550, 520, 510],
            "error_count": [25, 30, 28, 26],
            "bounce_count": [250, 240, 260, 255],
        })
        result = calculate_guardrails_multivariant(df)

        assert len(result["by_variant"]) == 3
        for v_name in ["variant_a", "variant_b", "variant_c"]:
            assert len(result["by_variant"][v_name]) == 2

        assert len(result["summary"]) == 2
