"""
Sequential Testing Module

Group Sequential Design을 사용한 실험 조기 종료 판단.
Lan-DeMets alpha spending approach를 사용합니다.

References:
    - Lan & DeMets (1983). Discrete sequential boundaries for clinical trials.
    - Jennison & Turnbull (2000). Group Sequential Methods with Applications to Clinical Trials.
"""

import math
import logging

import numpy as np
from scipy.stats import norm

from .config import config

logger = logging.getLogger("experimentos")


def alpha_spending(
    info_fraction: float,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
) -> float:
    """
    Lan-DeMets alpha spending function.

    Args:
        info_fraction: Information fraction t in (0, 1].
        alpha: Overall significance level.
        boundary_type: "obrien_fleming" or "pocock".

    Returns:
        Cumulative alpha spent at this information fraction.

    Raises:
        ValueError: If info_fraction is not in (0, 1] or boundary_type is unknown.
    """
    if info_fraction <= 0 or info_fraction > 1:
        raise ValueError(f"info_fraction must be in (0, 1], got {info_fraction}")

    if boundary_type == "obrien_fleming":
        # Lan-DeMets approximation of O'Brien-Fleming:
        # alpha*(t) = 2 - 2 * Phi(z_{alpha/2} / sqrt(t))
        z_alpha_half = norm.ppf(1 - alpha / 2)
        return float(2 - 2 * norm.cdf(z_alpha_half / math.sqrt(info_fraction)))

    elif boundary_type == "pocock":
        # Lan-DeMets approximation of Pocock:
        # alpha*(t) = alpha * ln(1 + (e - 1) * t)
        return float(alpha * math.log(1 + (math.e - 1) * info_fraction))

    else:
        raise ValueError(f"Unknown boundary_type: {boundary_type}. Use 'obrien_fleming' or 'pocock'.")


def calculate_boundaries(
    max_looks: int,
    info_fractions: list[float] | None = None,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
) -> list[dict]:
    """
    Calculate rejection boundaries at each look.

    Uses incremental alpha spending to derive the z-boundary at each analysis.

    Args:
        max_looks: Total planned number of analyses K.
        info_fractions: Information fractions [t1, t2, ..., tK].
                       If None, uses equal spacing [1/K, 2/K, ..., 1.0].
        alpha: Overall significance level.
        boundary_type: Boundary function type.

    Returns:
        List of dicts with keys: look, info_fraction, z_boundary,
        alpha_spent, cumulative_alpha, p_boundary.
    """
    if max_looks < 1:
        raise ValueError(f"max_looks must be >= 1, got {max_looks}")

    if info_fractions is None:
        info_fractions = [(k + 1) / max_looks for k in range(max_looks)]

    if len(info_fractions) != max_looks:
        raise ValueError(
            f"info_fractions length ({len(info_fractions)}) must equal max_looks ({max_looks})"
        )

    boundaries: list[dict] = []
    prev_cumulative = 0.0

    for k in range(max_looks):
        t = info_fractions[k]
        cumulative = alpha_spending(t, alpha, boundary_type)
        incremental = cumulative - prev_cumulative

        # Derive z-boundary from incremental alpha
        # For two-sided test: p_boundary = incremental, z = Phi^{-1}(1 - incremental/2)
        # Clamp incremental to avoid edge cases
        incremental = max(incremental, 1e-15)
        z_boundary = float(norm.ppf(1 - incremental / 2))

        boundaries.append(
            {
                "look": k + 1,
                "info_fraction": t,
                "z_boundary": z_boundary,
                "alpha_spent": incremental,
                "cumulative_alpha": cumulative,
                "p_boundary": incremental,
            }
        )
        prev_cumulative = cumulative

    return boundaries


def check_sequential(
    z_stat: float,
    current_look: int,
    max_looks: int,
    info_fraction: float,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
    previous_looks: list[dict] | None = None,
) -> dict:
    """
    Determine whether early stopping is justified at the current look.

    Args:
        z_stat: Current z-test statistic (absolute value is used).
        current_look: Current analysis number (1-indexed).
        max_looks: Total planned analyses.
        info_fraction: Current information fraction.
        alpha: Overall significance level.
        boundary_type: Boundary function type.
        previous_looks: Previous look results for alpha spending tracking.

    Returns:
        Dict with can_stop, decision, z_stat, z_boundary, alpha_spent_this_look,
        cumulative_alpha_spent, info_fraction, current_look, max_looks, message.
    """
    if current_look < 1 or current_look > max_looks:
        raise ValueError(f"current_look must be in [1, {max_looks}], got {current_look}")

    # Calculate boundaries up to current look
    # Build info_fractions using previous looks if available
    fractions = _build_info_fractions(current_look, max_looks, info_fraction, previous_looks)
    boundaries = calculate_boundaries(max_looks, fractions, alpha, boundary_type)

    # Get boundary for current look
    current_boundary = boundaries[current_look - 1]
    z_boundary = current_boundary["z_boundary"]
    alpha_spent = current_boundary["alpha_spent"]
    cumulative_alpha = current_boundary["cumulative_alpha"]

    abs_z = abs(z_stat)

    if abs_z >= z_boundary:
        # Reject null hypothesis — can stop early
        return {
            "can_stop": True,
            "decision": "reject_null",
            "z_stat": z_stat,
            "z_boundary": z_boundary,
            "alpha_spent_this_look": alpha_spent,
            "cumulative_alpha_spent": cumulative_alpha,
            "info_fraction": info_fraction,
            "current_look": current_look,
            "max_looks": max_looks,
            "message": (
                f"Look {current_look}/{max_looks}: |z| = {abs_z:.3f} >= boundary {z_boundary:.3f}. "
                f"통계적으로 유의한 차이가 확인되었습니다. 조기 종료가 가능합니다."
            ),
        }

    if current_look == max_looks:
        # Final look — fail to reject
        return {
            "can_stop": True,
            "decision": "fail_to_reject",
            "z_stat": z_stat,
            "z_boundary": z_boundary,
            "alpha_spent_this_look": alpha_spent,
            "cumulative_alpha_spent": cumulative_alpha,
            "info_fraction": info_fraction,
            "current_look": current_look,
            "max_looks": max_looks,
            "message": (
                f"Look {current_look}/{max_looks} (최종): |z| = {abs_z:.3f} < boundary {z_boundary:.3f}. "
                f"통계적으로 유의한 차이를 확인하지 못했습니다."
            ),
        }

    # Continue collecting data
    return {
        "can_stop": False,
        "decision": "continue",
        "z_stat": z_stat,
        "z_boundary": z_boundary,
        "alpha_spent_this_look": alpha_spent,
        "cumulative_alpha_spent": cumulative_alpha,
        "info_fraction": info_fraction,
        "current_look": current_look,
        "max_looks": max_looks,
        "message": (
            f"Look {current_look}/{max_looks}: |z| = {abs_z:.3f} < boundary {z_boundary:.3f}. "
            f"현재 데이터로는 결론을 내릴 수 없습니다. 추가 데이터 수집이 필요합니다."
        ),
    }


def analyze_sequential(
    control_users: int,
    control_conversions: int,
    treatment_users: int,
    treatment_conversions: int,
    target_sample_size: int,
    current_look: int,
    max_looks: int,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
    previous_looks: list[dict] | None = None,
) -> dict:
    """
    Run sequential analysis: compute z-stat, check boundaries, return full results.

    Args:
        control_users: Number of users in control group.
        control_conversions: Conversions in control group.
        treatment_users: Number of users in treatment group.
        treatment_conversions: Conversions in treatment group.
        target_sample_size: Total planned sample size (both groups combined).
        current_look: Current analysis number (1-indexed).
        max_looks: Total planned analyses.
        alpha: Overall significance level.
        boundary_type: Boundary function type.
        previous_looks: Previous look results.

    Returns:
        Dict with sequential_result, primary_result, boundaries, progress.
    """
    # 1. Calculate info fraction (clamp to small positive value to avoid alpha_spending(0))
    current_sample = control_users + treatment_users
    if target_sample_size > 0 and current_sample > 0:
        info_fraction = min(current_sample / target_sample_size, 1.0)
    elif target_sample_size > 0:
        info_fraction = 1e-6  # minimal positive value when no data yet
    else:
        info_fraction = 1.0

    # 2. Calculate z-statistic
    rate_c = control_conversions / control_users if control_users > 0 else 0.0
    rate_t = treatment_conversions / treatment_users if treatment_users > 0 else 0.0

    z_stat = _compute_z_stat(
        control_users, control_conversions, treatment_users, treatment_conversions
    )

    # 3. Primary result (standard analysis)
    abs_lift = rate_t - rate_c
    rel_lift = ((rate_t / rate_c) - 1) if rate_c > 0 else None
    p_value = float(2 * (1 - norm.cdf(abs(z_stat)))) if not np.isnan(z_stat) else 1.0

    primary_result = {
        "control_rate": rate_c,
        "treatment_rate": rate_t,
        "absolute_lift": abs_lift,
        "relative_lift": rel_lift,
        "z_stat": float(z_stat),
        "p_value": p_value,
        "is_significant": p_value < alpha,
    }

    # 4. Sequential check
    sequential_result = check_sequential(
        z_stat=z_stat,
        current_look=current_look,
        max_looks=max_looks,
        info_fraction=info_fraction,
        alpha=alpha,
        boundary_type=boundary_type,
        previous_looks=previous_looks,
    )

    # 5. Full boundaries for visualization
    fractions = _build_info_fractions(current_look, max_looks, info_fraction, previous_looks)
    boundaries = calculate_boundaries(max_looks, fractions, alpha, boundary_type)

    # 6. Progress info
    percentage = info_fraction * 100
    progress = {
        "current_sample": current_sample,
        "target_sample": target_sample_size,
        "info_fraction": info_fraction,
        "percentage": round(percentage, 1),
    }

    return {
        "sequential_result": sequential_result,
        "primary_result": primary_result,
        "boundaries": boundaries,
        "progress": progress,
    }


def _compute_z_stat(
    control_users: int,
    control_conversions: int,
    treatment_users: int,
    treatment_conversions: int,
) -> float:
    """Compute two-proportion z-test statistic."""
    n_c = control_users
    n_t = treatment_users

    if n_c <= 0 or n_t <= 0:
        return 0.0

    p_c = control_conversions / n_c
    p_t = treatment_conversions / n_t

    # Pooled proportion
    p_pool = (control_conversions + treatment_conversions) / (n_c + n_t)

    if p_pool <= 0 or p_pool >= 1:
        return 0.0

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))

    if se <= 0:
        return 0.0

    return (p_t - p_c) / se


def _build_info_fractions(
    current_look: int,
    max_looks: int,
    current_info_fraction: float,
    previous_looks: list[dict] | None,
) -> list[float]:
    """
    Build full list of info fractions for boundary calculation.

    Uses previous look fractions if available, then interpolates remaining.
    """
    fractions = [0.0] * max_looks

    # Fill from previous looks
    if previous_looks:
        for prev in previous_looks:
            look_idx = prev.get("look", 0) - 1
            if 0 <= look_idx < max_looks:
                fractions[look_idx] = prev.get("info_fraction", 0.0)

    # Set current look
    if 0 <= current_look - 1 < max_looks:
        fractions[current_look - 1] = current_info_fraction

    # Fill remaining future looks with linear interpolation from current to 1.0
    n_future = max_looks - current_look
    if n_future > 0:
        for i in range(n_future):
            k = current_look + i  # index in fractions array
            fractions[k] = current_info_fraction + (1.0 - current_info_fraction) * (i + 1) / n_future

    # Fill any missing early looks with equal spacing up to current
    for k in range(max_looks):
        if fractions[k] <= 0:
            fractions[k] = (k + 1) / max_looks

    # Ensure monotonically increasing
    for k in range(1, max_looks):
        if fractions[k] <= fractions[k - 1]:
            remaining = max_looks - k
            fractions[k] = fractions[k - 1] + (1.0 - fractions[k - 1]) / (remaining + 1)

    # Last fraction is always 1.0
    fractions[-1] = 1.0

    return fractions
