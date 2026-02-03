"""
Continuous Metric Analysis Module

Welch's t-test implementation for continuous metrics using sufficient statistics.
Inputs: metric_sum, metric_sum_sq, n for control and treatment.
"""

from typing import Dict, Tuple
import numpy as np
from scipy import stats
from .config import config

def calculate_continuous_lift(
    control_stats: Dict[str, float],
    treatment_stats: Dict[str, float],
    metric_name: str
) -> Dict:
    """
    Calculate lift and statistical significance for a continuous metric.
    
    Args:
        control_stats: {sum, sum_sq, n}
        treatment_stats: {sum, sum_sq, n}
        metric_name: Name of the metric (e.g., 'revenue')
        
    Returns:
        Dict results including means, p-value, CI, etc.
    """
    # 1. Extract stats
    n_c = control_stats["n"]
    sum_c = control_stats["sum"]
    sum_sq_c = control_stats["sum_sq"]
    
    n_t = treatment_stats["n"]
    sum_t = treatment_stats["sum"]
    sum_sq_t = treatment_stats["sum_sq"]
    
    # Check for empty or single samples
    if n_c < 2 or n_t < 2:
        return _empty_result(metric_name, "Insufficient data (n < 2)")

    # 2. Calculate means
    mean_c = sum_c / n_c
    mean_t = sum_t / n_t
    
    # 3. Calculate variances (sample variance formula from sufficient stats)
    # var = (sum_sq - (sum^2)/n) / (n - 1)
    
    # Numerical stability check for numerator
    ss_c = sum_sq_c - (sum_c**2 / n_c)
    ss_t = sum_sq_t - (sum_t**2 / n_t)
    
    # Clamp negative variance due to floating point noise
    if ss_c < -config.VAR_TOLERANCE or ss_t < -config.VAR_TOLERANCE:
        return _empty_result(metric_name, "Invalid variance (checksum failed)")
        
    ss_c = max(0.0, ss_c)
    ss_t = max(0.0, ss_t)
    
    var_c = ss_c / (n_c - 1)
    var_t = ss_t / (n_t - 1)
    
    # Zero variance edge case
    if var_c == 0 and var_t == 0:
        # If both predictable and equal means -> p=1.0, else p=0.0
        # For simplicity in A/B context, if means identical -> p=1.0
        p_value = 1.0 if mean_c == mean_t else 0.0
        std_err = 0.0
    else:
        # 4. Standard Error of difference (Welch's)
        std_err = np.sqrt(var_c/n_c + var_t/n_t)
        
        # 5. t-statistic and p-value
        if std_err == 0:
             p_value = 1.0 if mean_c == mean_t else 0.0
        else:
            t_stat = (mean_t - mean_c) / std_err
            
            # Welch-Satterthwaite degrees of freedom
            num = (var_c/n_c + var_t/n_t)**2
            den = (var_c/n_c)**2 / (n_c - 1) + (var_t/n_t)**2 / (n_t - 1)
            # handle den=0 edge case
            if den == 0:
                dof = n_c + n_t - 2
            else:
                dof = num / den
                
            p_value = stats.t.sf(np.abs(t_stat), dof) * 2  # two-sided
    
    # 6. Confidence Interval (95%)
    # For CI, critical value from t-distribution is better, but z-score approx ok for large N
    # Using t-dist for robustness
    if std_err > 0 and 'dof' in locals():
        crit_val = stats.t.ppf(1 - config.SIGNIFICANCE_ALPHA/2, dof)
        margin = crit_val * std_err
    else:
        margin = 0.0
        
    absolute_lift = mean_t - mean_c
    ci_lower = absolute_lift - margin
    ci_upper = absolute_lift + margin
    
    relative_lift = (absolute_lift / mean_c) if mean_c != 0 else 0.0

    return {
        "metric_name": metric_name,
        "is_valid": True,
        "control_mean": mean_c,
        "treatment_mean": mean_t,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "p_value": p_value,
        "ci_95": [ci_lower, ci_upper],
        "is_significant": p_value < config.SIGNIFICANCE_ALPHA
    }

def _empty_result(name: str, reason: str) -> Dict:
    return {
        "metric_name": name,
        "is_valid": False,
        "error": reason,
        "control_mean": 0.0,
        "treatment_mean": 0.0,
        "absolute_lift": 0.0,
        "relative_lift": 0.0,
        "p_value": 1.0,
        "ci_95": [0.0, 0.0],
        "is_significant": False
    }
