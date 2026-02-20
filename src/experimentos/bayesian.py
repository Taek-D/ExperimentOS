"""
Bayesian Analysis Module

Provides Bayesian interpretation of results (Probability of Being Best).
Logic is strictly informational and does NOT affect decision rules.
Uses deterministic simulation with fixed seed.
"""

import numpy as np
from scipy import stats
from .config import config

def calculate_beta_binomial(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int
) -> dict:
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

def calculate_beta_binomial_multivariant(
    control_conversions: int,
    control_total: int,
    treatments: list[dict],
) -> dict:
    """
    Multi-variant Beta-Binomial Bayesian analysis.

    Calculates P(variant > control) for each variant, and P(being best) across all variants.

    Args:
        control_conversions: Control group conversions
        control_total: Control group total users
        treatments: List of {"name": str, "conversions": int, "total": int}

    Returns:
        dict: {
            "vs_control": {"variant_a": {"prob_beats_control": float, "expected_loss": float}},
            "prob_being_best": {"control": float, "variant_a": float, ...}
        }
    """
    rng = np.random.default_rng(config.BAYES_SEED)

    alpha_c = 1 + control_conversions
    beta_c = 1 + control_total - control_conversions
    samples_c = rng.beta(alpha_c, beta_c, size=config.BAYES_SAMPLES)

    vs_control: dict[str, dict] = {}
    all_samples: dict[str, np.ndarray] = {"control": samples_c}

    for t in treatments:
        name = t["name"]
        alpha_t = 1 + t["conversions"]
        beta_t = 1 + t["total"] - t["conversions"]
        samples_t = rng.beta(alpha_t, beta_t, size=config.BAYES_SAMPLES)
        all_samples[name] = samples_t

        prob_beats = float(np.mean(samples_t > samples_c))
        exp_loss = float(np.mean(np.maximum(samples_c - samples_t, 0)))

        vs_control[name] = {
            "prob_beats_control": prob_beats,
            "expected_loss": exp_loss,
            "posterior": {"alpha": alpha_t, "beta": beta_t},
        }

    # P(being best) for each variant including control
    variant_names = list(all_samples.keys())
    stacked = np.stack([all_samples[n] for n in variant_names], axis=0)  # (K, N)
    best_indices = np.argmax(stacked, axis=0)  # (N,)
    prob_being_best: dict[str, float] = {}
    for i, name in enumerate(variant_names):
        prob_being_best[name] = float(np.mean(best_indices == i))

    return {
        "vs_control": vs_control,
        "prob_being_best": prob_being_best,
        "control_posterior": {"alpha": alpha_c, "beta": beta_c},
    }


def calculate_continuous_bayes(
    control_stats: dict,
    treatment_stats: dict
) -> dict:
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
