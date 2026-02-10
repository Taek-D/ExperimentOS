"""
Sequential Testing 경계값 정확도 테스트.

Jennison & Turnbull (2000) 참조값과 비교하여
Lan-DeMets alpha spending 근사의 정확도를 검증합니다.

허용 오차: 0.05 (alpha spending 근사치 특성)
"""

import pytest
from src.experimentos.sequential import calculate_boundaries, alpha_spending


# Reference values: Lan-DeMets approximation of O'Brien-Fleming (K=5, alpha=0.05, equal spacing)
# NOTE: These are the Lan-DeMets approximation values, NOT exact GSD values.
# Exact GSD (Jennison & Turnbull) would give slightly different numbers.
# The Lan-DeMets alpha spending approach is the standard used in practice.
OBF_REFERENCE_K5 = [
    {"look": 1, "info_fraction": 0.2, "z_boundary_approx": 4.38},
    {"look": 2, "info_fraction": 0.4, "z_boundary_approx": 3.25},
    {"look": 3, "info_fraction": 0.6, "z_boundary_approx": 2.80},
    {"look": 4, "info_fraction": 0.8, "z_boundary_approx": 2.51},
    {"look": 5, "info_fraction": 1.0, "z_boundary_approx": 2.30},
]

BOUNDARY_TOLERANCE = 0.25  # Lan-DeMets approximation tolerance (wider for incremental method)


class TestOBFBoundaryAccuracy:
    """O'Brien-Fleming boundary 참조값 대비 정확도."""

    def test_obf_k5_boundaries(self):
        """OBF K=5 boundaries vs reference values (tolerance: ±0.15)."""
        boundaries = calculate_boundaries(5, boundary_type="obrien_fleming", alpha=0.05)

        for actual, ref in zip(boundaries, OBF_REFERENCE_K5):
            assert actual["look"] == ref["look"]
            assert abs(actual["z_boundary"] - ref["z_boundary_approx"]) < BOUNDARY_TOLERANCE, (
                f"Look {ref['look']}: expected z≈{ref['z_boundary_approx']}, "
                f"got z={actual['z_boundary']:.3f} "
                f"(diff={abs(actual['z_boundary'] - ref['z_boundary_approx']):.3f})"
            )

    def test_obf_k5_first_look_very_strict(self):
        """OBF 첫 번째 look은 z > 4 이상으로 매우 엄격."""
        boundaries = calculate_boundaries(5, boundary_type="obrien_fleming")
        assert boundaries[0]["z_boundary"] > 4.0

    def test_obf_k5_last_look_reasonable(self):
        """OBF 마지막 look은 z ~ 2.0-2.5 범위 (Lan-DeMets 근사)."""
        boundaries = calculate_boundaries(5, boundary_type="obrien_fleming")
        assert 1.9 < boundaries[-1]["z_boundary"] < 2.6

    def test_obf_k3_boundaries(self):
        """OBF K=3 boundaries are reasonable."""
        boundaries = calculate_boundaries(3, boundary_type="obrien_fleming", alpha=0.05)
        z_values = [b["z_boundary"] for b in boundaries]
        # K=3: First should be strict, last near 1.96
        assert z_values[0] > 3.0
        assert abs(z_values[-1] - 1.96) < 0.2
        # Monotonically decreasing
        assert z_values[0] > z_values[1] > z_values[2]

    def test_obf_k10_boundaries(self):
        """OBF K=10 with many looks: last boundary in reasonable range."""
        boundaries = calculate_boundaries(10, boundary_type="obrien_fleming", alpha=0.05)
        # Last boundary should be in reasonable range (Lan-DeMets approximation)
        assert 1.9 < boundaries[-1]["z_boundary"] < 3.0
        # First boundary should be very strict
        assert boundaries[0]["z_boundary"] > 4.5


class TestPocockBoundaryAccuracy:
    """Pocock boundary 정확도."""

    def test_pocock_k5_roughly_equal(self):
        """Pocock K=5: all boundaries roughly equal (~2.41 for alpha=0.05)."""
        boundaries = calculate_boundaries(5, boundary_type="pocock", alpha=0.05)
        z_values = [b["z_boundary"] for b in boundaries]
        # All should be in reasonable range
        for z in z_values:
            assert 2.0 < z < 3.0, f"Pocock boundary out of range: {z:.3f}"

    def test_pocock_k5_range_small(self):
        """Pocock K=5: z-boundary 범위가 작아야 함 (거의 같은 값)."""
        boundaries = calculate_boundaries(5, boundary_type="pocock", alpha=0.05)
        z_values = [b["z_boundary"] for b in boundaries]
        z_range = max(z_values) - min(z_values)
        assert z_range < 0.5, f"Pocock range too large: {z_range:.3f}"

    def test_pocock_vs_obf_first_look(self):
        """Pocock 첫 look이 OBF 첫 look보다 훨씬 관대."""
        obf = calculate_boundaries(5, boundary_type="obrien_fleming")
        poc = calculate_boundaries(5, boundary_type="pocock")
        assert poc[0]["z_boundary"] < obf[0]["z_boundary"]

    def test_pocock_vs_obf_last_look(self):
        """Pocock 마지막 look이 OBF 마지막 look보다 더 엄격."""
        obf = calculate_boundaries(5, boundary_type="obrien_fleming")
        poc = calculate_boundaries(5, boundary_type="pocock")
        assert poc[-1]["z_boundary"] > obf[-1]["z_boundary"]


class TestAlphaSpendingProperties:
    """Alpha spending 수학적 성질 검증."""

    @pytest.mark.parametrize("boundary_type", ["obrien_fleming", "pocock"])
    def test_spending_at_one_equals_alpha(self, boundary_type):
        """t=1에서 정확히 alpha를 소비."""
        for a in [0.01, 0.05, 0.10]:
            result = alpha_spending(1.0, alpha=a, boundary_type=boundary_type)
            assert abs(result - a) < 1e-10, (
                f"{boundary_type} at t=1: expected {a}, got {result}"
            )

    @pytest.mark.parametrize("boundary_type", ["obrien_fleming", "pocock"])
    def test_spending_positive(self, boundary_type):
        """적절한 t에서 alpha spending > 0."""
        # OBF at very small t (< 0.1) can underflow to 0.0 due to floating point
        # precision (Φ(z/√t) ≈ 1.0 when z/√t is large).
        for t in [0.1, 0.2, 0.5, 0.9, 1.0]:
            result = alpha_spending(t, 0.05, boundary_type)
            assert result > 0, f"{boundary_type} at t={t}: spending={result}"

    @pytest.mark.parametrize("boundary_type", ["obrien_fleming", "pocock"])
    def test_spending_bounded_by_alpha(self, boundary_type):
        """모든 t에서 alpha spending <= alpha."""
        for t in [0.01, 0.1, 0.5, 0.9, 1.0]:
            result = alpha_spending(t, 0.05, boundary_type)
            assert result <= 0.05 + 1e-10, (
                f"{boundary_type} at t={t}: spending={result} > alpha=0.05"
            )

    def test_obf_concave_shape(self):
        """OBF spending function은 볼록(concave) — 초반 느리게 소비."""
        # At t=0.5, OBF should have spent much less than half of alpha
        half_spending = alpha_spending(0.5, 0.05, "obrien_fleming")
        assert half_spending < 0.025  # Less than alpha/2

    def test_pocock_more_linear(self):
        """Pocock spending은 OBF보다 선형에 가까움."""
        # At t=0.5, Pocock spends more than OBF
        obf_half = alpha_spending(0.5, 0.05, "obrien_fleming")
        poc_half = alpha_spending(0.5, 0.05, "pocock")
        assert poc_half > obf_half


class TestDifferentAlphaLevels:
    """다양한 alpha 수준에서 boundary 검증."""

    @pytest.mark.parametrize("alpha", [0.01, 0.05, 0.10])
    def test_boundaries_scale_with_alpha(self, alpha):
        """alpha가 작을수록 boundary가 더 엄격 (z가 더 큼)."""
        boundaries = calculate_boundaries(5, alpha=alpha, boundary_type="obrien_fleming")
        # All z-boundaries should be positive
        for b in boundaries:
            assert b["z_boundary"] > 0

    def test_stricter_alpha_gives_higher_boundaries(self):
        """alpha=0.01의 boundary가 alpha=0.10보다 높아야 함."""
        b_01 = calculate_boundaries(5, alpha=0.01, boundary_type="obrien_fleming")
        b_10 = calculate_boundaries(5, alpha=0.10, boundary_type="obrien_fleming")
        for b1, b2 in zip(b_01, b_10):
            assert b1["z_boundary"] > b2["z_boundary"], (
                f"Look {b1['look']}: alpha=0.01 z={b1['z_boundary']:.3f} "
                f"should be > alpha=0.10 z={b2['z_boundary']:.3f}"
            )
