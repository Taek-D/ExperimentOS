"""
Sequential Testing 핵심 로직 단위 테스트.

alpha_spending, calculate_boundaries, check_sequential, analyze_sequential 테스트.
"""

import pytest
import math
from src.experimentos.sequential import (
    alpha_spending,
    calculate_boundaries,
    check_sequential,
    analyze_sequential,
    _compute_z_stat,
)


class TestAlphaSpending:
    """alpha_spending() 함수 테스트."""

    def test_obf_at_one_equals_alpha(self):
        """t=1에서 alpha_spent = alpha."""
        result = alpha_spending(1.0, alpha=0.05, boundary_type="obrien_fleming")
        assert abs(result - 0.05) < 1e-10

    def test_obf_monotonic_increasing(self):
        """OBF alpha spending은 단조 증가해야 한다."""
        fractions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        values = [alpha_spending(t, 0.05, "obrien_fleming") for t in fractions]
        for i in range(1, len(values)):
            assert values[i] > values[i - 1], f"Not monotonic at t={fractions[i]}"

    def test_obf_small_fraction_near_zero(self):
        """OBF는 작은 info_fraction에서 매우 작은 alpha를 소비한다."""
        result = alpha_spending(0.1, alpha=0.05, boundary_type="obrien_fleming")
        assert result < 0.001  # OBF is very conservative early on

    def test_pocock_at_one_equals_alpha(self):
        """Pocock: t=1에서 alpha_spent = alpha."""
        result = alpha_spending(1.0, alpha=0.05, boundary_type="pocock")
        assert abs(result - 0.05) < 1e-10

    def test_pocock_monotonic_increasing(self):
        """Pocock alpha spending은 단조 증가."""
        fractions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        values = [alpha_spending(t, 0.05, "pocock") for t in fractions]
        for i in range(1, len(values)):
            assert values[i] > values[i - 1]

    def test_pocock_spends_more_early_than_obf(self):
        """Pocock은 OBF보다 초반에 더 많은 alpha를 소비한다."""
        t = 0.2
        obf = alpha_spending(t, 0.05, "obrien_fleming")
        poc = alpha_spending(t, 0.05, "pocock")
        assert poc > obf

    def test_invalid_fraction_raises(self):
        """info_fraction <= 0 또는 > 1이면 ValueError."""
        with pytest.raises(ValueError):
            alpha_spending(0.0, 0.05, "obrien_fleming")
        with pytest.raises(ValueError):
            alpha_spending(-0.1, 0.05, "obrien_fleming")
        with pytest.raises(ValueError):
            alpha_spending(1.1, 0.05, "obrien_fleming")

    def test_unknown_boundary_type_raises(self):
        """알 수 없는 boundary_type이면 ValueError."""
        with pytest.raises(ValueError):
            alpha_spending(0.5, 0.05, "unknown_type")


class TestCalculateBoundaries:
    """calculate_boundaries() 함수 테스트."""

    def test_count_matches_max_looks(self):
        """boundary 개수 = max_looks."""
        boundaries = calculate_boundaries(5, alpha=0.05)
        assert len(boundaries) == 5

    def test_obf_early_boundaries_stricter(self):
        """OBF: 초반 z-boundary가 후반보다 크다 (더 엄격)."""
        boundaries = calculate_boundaries(5, boundary_type="obrien_fleming")
        z_values = [b["z_boundary"] for b in boundaries]
        # z-boundary should be decreasing (stricter early, relaxed later)
        for i in range(1, len(z_values)):
            assert z_values[i] < z_values[i - 1], (
                f"OBF boundary not decreasing: look {i}: {z_values[i-1]:.3f} -> {z_values[i]:.3f}"
            )

    def test_pocock_boundaries_roughly_equal(self):
        """Pocock: boundary들이 대략 비슷해야 한다."""
        boundaries = calculate_boundaries(5, boundary_type="pocock")
        z_values = [b["z_boundary"] for b in boundaries]
        # Pocock boundaries should be within a reasonable range of each other
        z_range = max(z_values) - min(z_values)
        assert z_range < 1.0, f"Pocock boundaries too variable: range={z_range:.3f}"

    def test_info_fractions_equal_spacing(self):
        """info_fractions=None이면 균등 분할."""
        boundaries = calculate_boundaries(5)
        fractions = [b["info_fraction"] for b in boundaries]
        expected = [0.2, 0.4, 0.6, 0.8, 1.0]
        for actual, exp in zip(fractions, expected):
            assert abs(actual - exp) < 1e-10

    def test_custom_info_fractions(self):
        """사용자 정의 info_fractions."""
        fracs = [0.1, 0.3, 0.5, 0.7, 1.0]
        boundaries = calculate_boundaries(5, info_fractions=fracs)
        for b, f in zip(boundaries, fracs):
            assert b["info_fraction"] == f

    def test_single_look(self):
        """max_looks=1이면 boundary 1개, t=1.0."""
        boundaries = calculate_boundaries(1)
        assert len(boundaries) == 1
        assert boundaries[0]["info_fraction"] == 1.0
        # Single-look z-boundary should be close to standard z_{alpha/2}
        assert abs(boundaries[0]["z_boundary"] - 1.96) < 0.05

    def test_cumulative_alpha_monotonic(self):
        """누적 alpha는 단조 증가."""
        boundaries = calculate_boundaries(5, boundary_type="obrien_fleming")
        cum_alphas = [b["cumulative_alpha"] for b in boundaries]
        for i in range(1, len(cum_alphas)):
            assert cum_alphas[i] >= cum_alphas[i - 1]

    def test_last_cumulative_alpha_equals_alpha(self):
        """마지막 look의 cumulative_alpha = alpha."""
        boundaries = calculate_boundaries(5, alpha=0.05, boundary_type="obrien_fleming")
        assert abs(boundaries[-1]["cumulative_alpha"] - 0.05) < 1e-10

    def test_invalid_max_looks_raises(self):
        """max_looks < 1이면 ValueError."""
        with pytest.raises(ValueError):
            calculate_boundaries(0)

    def test_mismatched_fractions_raises(self):
        """info_fractions 길이 != max_looks이면 ValueError."""
        with pytest.raises(ValueError):
            calculate_boundaries(5, info_fractions=[0.2, 0.5, 1.0])


class TestCheckSequential:
    """check_sequential() 함수 테스트."""

    def test_reject_when_z_exceeds_boundary(self):
        """z > boundary이면 can_stop=True, decision=reject_null."""
        result = check_sequential(
            z_stat=5.0,  # Very large z
            current_look=1,
            max_looks=5,
            info_fraction=0.2,
        )
        assert result["can_stop"] is True
        assert result["decision"] == "reject_null"

    def test_continue_when_z_below_boundary(self):
        """z < boundary이면 continue."""
        result = check_sequential(
            z_stat=0.5,  # Small z
            current_look=1,
            max_looks=5,
            info_fraction=0.2,
        )
        assert result["can_stop"] is False
        assert result["decision"] == "continue"

    def test_fail_to_reject_at_final_look(self):
        """마지막 look에서 z < boundary이면 fail_to_reject."""
        result = check_sequential(
            z_stat=0.5,
            current_look=5,
            max_looks=5,
            info_fraction=1.0,
        )
        assert result["can_stop"] is True
        assert result["decision"] == "fail_to_reject"

    def test_reject_at_final_look(self):
        """마지막 look에서 z > boundary이면 reject_null."""
        result = check_sequential(
            z_stat=3.0,
            current_look=5,
            max_looks=5,
            info_fraction=1.0,
        )
        assert result["can_stop"] is True
        assert result["decision"] == "reject_null"

    def test_negative_z_stat_uses_absolute(self):
        """음수 z-stat도 절대값으로 비교."""
        result = check_sequential(
            z_stat=-5.0,
            current_look=1,
            max_looks=5,
            info_fraction=0.2,
        )
        assert result["can_stop"] is True
        assert result["decision"] == "reject_null"

    def test_message_contains_look_info(self):
        """메시지에 look 정보가 포함."""
        result = check_sequential(
            z_stat=1.0,
            current_look=2,
            max_looks=5,
            info_fraction=0.4,
        )
        assert "2/5" in result["message"]

    def test_invalid_current_look_raises(self):
        """current_look 범위 초과 시 ValueError."""
        with pytest.raises(ValueError):
            check_sequential(z_stat=1.0, current_look=0, max_looks=5, info_fraction=0.2)
        with pytest.raises(ValueError):
            check_sequential(z_stat=1.0, current_look=6, max_looks=5, info_fraction=0.2)

    def test_with_previous_looks(self):
        """previous_looks 제공 시 정상 동작."""
        prev = [{"look": 1, "z_stat": 1.2, "info_fraction": 0.2, "cumulative_alpha_spent": 0.0001}]
        result = check_sequential(
            z_stat=1.5,
            current_look=2,
            max_looks=5,
            info_fraction=0.4,
            previous_looks=prev,
        )
        assert result["current_look"] == 2
        assert "decision" in result


class TestAnalyzeSequential:
    """analyze_sequential() 통합 함수 테스트."""

    def test_integration_returns_all_keys(self):
        """통합 함수가 모든 필수 키를 반환."""
        result = analyze_sequential(
            control_users=5000,
            control_conversions=600,
            treatment_users=5100,
            treatment_conversions=680,
            target_sample_size=20000,
            current_look=2,
            max_looks=5,
        )
        assert "sequential_result" in result
        assert "primary_result" in result
        assert "boundaries" in result
        assert "progress" in result

    def test_progress_calculation(self):
        """progress 계산 정확도."""
        result = analyze_sequential(
            control_users=5000,
            control_conversions=600,
            treatment_users=5000,
            treatment_conversions=650,
            target_sample_size=20000,
            current_look=2,
            max_looks=5,
        )
        progress = result["progress"]
        assert progress["current_sample"] == 10000
        assert progress["target_sample"] == 20000
        assert abs(progress["info_fraction"] - 0.5) < 1e-10
        assert abs(progress["percentage"] - 50.0) < 0.1

    def test_primary_result_contains_rates(self):
        """primary_result에 전환율 정보 포함."""
        result = analyze_sequential(
            control_users=1000,
            control_conversions=100,
            treatment_users=1000,
            treatment_conversions=120,
            target_sample_size=5000,
            current_look=1,
            max_looks=5,
        )
        primary = result["primary_result"]
        assert abs(primary["control_rate"] - 0.1) < 1e-10
        assert abs(primary["treatment_rate"] - 0.12) < 1e-10
        assert primary["absolute_lift"] == pytest.approx(0.02, abs=1e-10)

    def test_boundaries_count_matches_max_looks(self):
        """boundaries 수 = max_looks."""
        result = analyze_sequential(
            control_users=1000,
            control_conversions=100,
            treatment_users=1000,
            treatment_conversions=120,
            target_sample_size=5000,
            current_look=1,
            max_looks=3,
        )
        assert len(result["boundaries"]) == 3

    def test_large_effect_triggers_reject(self):
        """큰 효과 크기 → reject_null."""
        result = analyze_sequential(
            control_users=5000,
            control_conversions=500,
            treatment_users=5000,
            treatment_conversions=800,  # Large effect
            target_sample_size=10000,
            current_look=5,
            max_looks=5,
        )
        seq = result["sequential_result"]
        assert seq["decision"] == "reject_null"

    def test_zero_users_handled(self):
        """users=0일 때 에러 없이 처리."""
        result = analyze_sequential(
            control_users=0,
            control_conversions=0,
            treatment_users=0,
            treatment_conversions=0,
            target_sample_size=10000,
            current_look=1,
            max_looks=5,
        )
        assert result["primary_result"]["z_stat"] == 0.0


class TestComputeZStat:
    """_compute_z_stat() helper 테스트."""

    def test_equal_rates_gives_zero(self):
        """동일 전환율 → z ≈ 0."""
        z = _compute_z_stat(1000, 100, 1000, 100)
        assert abs(z) < 0.01

    def test_higher_treatment_gives_positive(self):
        """treatment 전환율 높으면 z > 0."""
        z = _compute_z_stat(1000, 100, 1000, 150)
        assert z > 0

    def test_lower_treatment_gives_negative(self):
        """treatment 전환율 낮으면 z < 0."""
        z = _compute_z_stat(1000, 150, 1000, 100)
        assert z < 0

    def test_zero_users_returns_zero(self):
        """users=0이면 z=0."""
        assert _compute_z_stat(0, 0, 1000, 100) == 0.0
        assert _compute_z_stat(1000, 100, 0, 0) == 0.0
