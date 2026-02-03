"""
Bayesian Analysis Module

Provides Bayesian interpretation of results (Probability of Being Best).
Logic is strictly informational and does NOT affect decision rules.
Uses deterministic simulation with fixed seed.
"""

from typing import Dict, Tuple
import numpy as np
from scipy import stats
from .config import config

def calculate_beta_binomial(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int
) -> Dict:
    """
    Calculate P(Treatment > Control) using Beta-Binomial model.
    Prior: Beta(1, 1) [Uniform]
    """
    # Posterior parameters
    alpha_c = 1 + control_conversions
    beta_c = 1 + control_total - control_conversions
    
    alpha_t = 1 + treatment_conversions
    beta_t = 1 + treatment_total - treatment_conversions
    
    # Simulation (Fast & Robust)
    rng = np.random.default_rng(config.BAYES_SEED)
    samples_c = rng.beta(alpha_c, beta_c, size=config.BAYES_SAMPLES)
    samples_t = rng.beta(alpha_t, beta_t, size=config.BAYES_SAMPLES)
    
    prob_t_wins = np.mean(samples_t > samples_c)
    expected_loss = np.mean(np.maximum(samples_c - samples_t, 0))
    
    return {
        "prob_treatment_beats_control": float(prob_t_wins),
        "expected_loss": float(expected_loss),
        "control_posterior": {"alpha": alpha_c, "beta": beta_c},
        "treatment_posterior": {"alpha": alpha_t, "beta": beta_t}
    }

def calculate_continuous_bayes(
    control_stats: Dict,
    treatment_stats: Dict
) -> Dict:
    """
    Calculate P(Treatment > Control) for continuous metrics.
    Approximate using Normal distribution of means with simulated sampling.
    """
    n_c = control_stats["n"]
    mu_c = control_stats["sum"] / n_c
    # Sample variance approx
    ss_c = max(0, control_stats["sum_sq"] - (control_stats["sum"]**2 / n_c))
    var_c = ss_c / (n_c - 1) if n_c > 1 else 0
    std_err_c = np.sqrt(var_c / n_c) if n_c > 0 else 0
    
    n_t = treatment_stats["n"]
    mu_t = treatment_stats["sum"] / n_t
    ss_t = max(0, treatment_stats["sum_sq"] - (treatment_stats["sum"]**2 / n_t))
    var_t = ss_t / (n_t - 1) if n_t > 1 else 0
    std_err_t = np.sqrt(var_t / n_t) if n_t > 0 else 0
    
    if std_err_c == 0 and std_err_t == 0:
         # Deterministic comparison
         prob = 1.0 if mu_t > mu_c else 0.0
         return {"prob_treatment_beats_control": prob, "expected_loss": 0.0}

    # Simulation
    rng = np.random.default_rng(config.BAYES_SEED)
    samples_c = rng.normal(mu_c, std_err_c, size=config.BAYES_SAMPLES)
    samples_t = rng.normal(mu_t, std_err_t, size=config.BAYES_SAMPLES)
    
    prob_t_wins = np.mean(samples_t > samples_c)
    expected_loss = np.mean(np.maximum(samples_c - samples_t, 0))
    
    return {
        "prob_treatment_beats_control": float(prob_t_wins),
        "expected_loss": float(expected_loss)
    }
