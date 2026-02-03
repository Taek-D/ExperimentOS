"""
Power Analysis Module

Provides sample size calculators using statsmodels.
"""

import numpy as np
import statsmodels.stats.power as smp
import statsmodels.stats.api as sms
from statsmodels.stats.proportion import proportion_effectsize

def calculate_sample_size_conversion(
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.8,
    ratio: float = 1.0
) -> int:
    """
    Calculate sample size for comparison of two independent proportions (Z-test).
    Uses statsmodels NormalIndPower (Arcsine transformation approximation) or GofChisquarePower.
    Actually, statsmodels 'zt_ind_solve_power' is most standard for Z-test.
    """
    if baseline_rate <= 0 or baseline_rate >= 1:
        return 0
    if mde == 0:
        return 0
        
    p1 = baseline_rate
    p2 = p1 * (1 + mde)
    
    if p2 > 1.0: p2 = 1.0
    if p2 < 0.0: p2 = 0.0
    
    # Method 1: Cohen's h (Arcsin) - Standard for 'NormalIndPower'
    # proportion_effectsize(prop1, prop2) calculates 2 * (arcsin(sqrt(prop1)) - arcsin(sqrt(prop2)))
    h = proportion_effectsize(p2, p1)
    h = abs(h)
    
    if h == 0:
        return 0
        
    # solve_power returns N per group
    n = smp.NormalIndPower().solve_power(
        effect_size=h, 
        alpha=alpha, 
        power=power, 
        ratio=ratio,
        alternative='two-sided'
    )
    
    return int(np.ceil(n))


def calculate_sample_size_continuous(
    std_dev: float,
    mde_abs: float,
    alpha: float = 0.05,
    power: float = 0.8,
    ratio: float = 1.0
) -> int:
    """
    Calculate sample size for comparison of two means (T-test).
    """
    if mde_abs == 0:
        return 0
    
    # Effect size d = (mean1 - mean2) / std_dev
    # Assuming standard deviation is pooled/similar
    d = abs(mde_abs) / std_dev
    
    if d == 0:
        return 0
        
    # T-test power (more accurate than Z-test for smaller N, converges for large N)
    n = smp.TTestIndPower().solve_power(
        effect_size=d, 
        alpha=alpha, 
        power=power, 
        ratio=ratio, 
        alternative='two-sided'
    )
        
    return int(np.ceil(n))
