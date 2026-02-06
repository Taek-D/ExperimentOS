"""
분석 모듈

Primary metric(전환율) 및 Guardrail 분석 로직
"""

import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
try:
    from statsmodels.stats.multitest import multipletests
except ImportError:
    multipletests = None

from scipy.stats import chi2_contingency
from typing import Any
import logging
import itertools

from .config import (
    GUARDRAIL_WORSENED_THRESHOLD, 
    GUARDRAIL_SEVERE_THRESHOLD,
    MULTIPLE_TESTING_METHOD
)
from .continuous_analysis import calculate_continuous_lift
from .bayesian import calculate_beta_binomial, calculate_continuous_bayes

logger = logging.getLogger("experimentos")


def _correct_p_values(p_values: list[float], method: str = MULTIPLE_TESTING_METHOD) -> list[float]:
    """
    Apply p-value correction for multiple comparisons.
    Methods: 'bonferroni', 'holm', 'fdr_bh' (Benjamini-Hochberg), 'none'
    """
    if not p_values or method == 'none':
        return p_values
    
    # Use statsmodels if available
    if multipletests:
        try:
            _, pvals_corrected, _, _ = multipletests(p_values, method=method)
            return list(pvals_corrected.tolist())
        except Exception as e:
            logger.warning(f"Statsmodels correction failed ({e}), falling back to manual.")
    
    # Manual fallback implementations
    n = len(p_values)
    if method == 'bonferroni':
        return [min(1.0, p * n) for p in p_values]
    elif method == 'holm':
        # Holm-Bonferroni
        # Sort p-values, apply p * (n - rank + 1), enforce monotonicity
        indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
        corrected = [0.0] * n
        for i, (orig_idx, p) in enumerate(indexed_p):
            rank = i + 1
            corr_p = min(1.0, p * (n - rank + 1))
            # Enforce monotonicity (step-down)
            if i > 0:
                corr_p = max(corr_p, corrected[indexed_p[i-1][0]])
            corrected[orig_idx] = corr_p
        return corrected
    elif method == 'fdr_bh':
        # Benjamini-Hochberg
        # p * n / rank
        indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
        corrected = [0.0] * n
        # Step-up procedure (start from largest p-value)
        # Note: Standard BH controls FDR, adjusted p-values are slightly different
        # Standard definition: p_adj = min(min(p_val * m / rank, 1), p_adj_next)
        prev_p_adj = 1.0
        result_map = {}
        
        for k in range(n, 0, -1):
            idx_in_sorted = k - 1
            orig_idx, p = indexed_p[idx_in_sorted]
            rank = k
            p_adj = min(1.0, p * n / rank)
            p_adj = min(p_adj, prev_p_adj)
            result_map[orig_idx] = p_adj
            prev_p_adj = p_adj
            
        return [result_map[i] for i in range(n)]
        
    return p_values

def analyze_multivariant(df: pd.DataFrame, correction_method: str = MULTIPLE_TESTING_METHOD) -> dict[str, Any]:
    """
    Multi-variant Primary Metric Analysis.
    Performs overall Chi-square test and multiple pairwise Z-tests vs Control.
    
    Args:
        df: DataFrame with 'variant', 'users', 'conversions'.
            Must contain 'control' variant.
        correction_method: Method for p-value correction ('bonferroni', 'holm', 'fdr_bh', 'none')
            
    Returns:
        dict: {
            "overall": { ... },
            "variants": { 
                "variant_name": { ..., "p_value_corrected": float } 
            },
            "all_pairs": [
                { "variant_a": str, "variant_b": str, "p_value": float, "p_value_corrected": float, ... }
            ],
            "correction_method": str
        }
    """
    results: dict[str, Any] = {
        "overall": {},
        "variants": {},
        "all_pairs": [],
        "correction_method": correction_method
    }
    
    # 1. Overall Chi-square Test for Independence
    if len(df) < 2:
        return results

    try:
        # Contingency table logic...
        contingency_table = []
        variant_names = []
        
        for _, row in df.iterrows():
            conv = int(row["conversions"])
            users = int(row["users"])
            non_conv = max(0, users - conv)
            contingency_table.append([conv, non_conv])
            variant_names.append(row["variant"])
            
        chi2, overall_p, dof, expected = chi2_contingency(contingency_table)

        results["overall"] = {
            "chi2_stat": chi2,
            "p_value": float(overall_p),
            "dof": dof,
            "is_significant": bool(overall_p < 0.05)
        }
        
    except Exception as e:
        logger.error(f"Chi-square test failed: {e}")
        results["overall"] = {"error": str(e), "p_value": 1.0}

    # 2. Pairwise vs Control & Correction
    control_rows = df[df["variant"] == "control"]
    
    # Data collection for pairwise
    treatments: list[dict[str, Any]] = []
    
    if not control_rows.empty:
        control_row = control_rows.iloc[0]
        users_c = int(control_row["users"])
        conv_c = int(control_row["conversions"])
        rate_c = conv_c / users_c if users_c > 0 else 0.0
        
        results["control_stats"] = {
            "users": users_c,
            "conversions": conv_c,
            "rate": rate_c
        }

        # Calculate vs Control first
        vs_control_p_values: list[float] = []
        vs_control_keys: list[str] = []
        
        treatment_df = df[df["variant"] != "control"]
        
        for _, row in treatment_df.iterrows():
            v_name = row["variant"]
            users_t = int(row["users"])
            conv_t = int(row["conversions"])
            rate_t = conv_t / users_t if users_t > 0 else 0.0
            
            abs_lift = rate_t - rate_c
            rel_lift = ((rate_t / rate_c) - 1) if rate_c > 0 else None
            
            p_val = 1.0
            ci_lower, ci_upper = 0.0, 0.0

            if users_c > 0 and users_t > 0:
                try:
                    counts = np.array([conv_t, conv_c])
                    nobs = np.array([users_t, users_c])
                    _, p_val_raw = proportions_ztest(count=counts, nobs=nobs, alternative='two-sided')
                    p_val = float(p_val_raw)
                    ci_lower, ci_upper = confint_proportions_2indep(
                        conv_t, users_t, conv_c, users_c, compare='diff', alpha=0.05, method='agresti-caffo'
                    )
                except Exception:
                    pass

            vs_control_p_values.append(float(p_val))
            vs_control_keys.append(v_name)
            
            results["variants"][v_name] = {
                "users": users_t,
                "conversions": conv_t,
                "rate": rate_t,
                "absolute_lift": abs_lift,
                "relative_lift": rel_lift,
                "ci_95": [ci_lower, ci_upper],
                "p_value": p_val,
                # corrected p-value will be updated momentarily
                "is_significant": p_val < 0.05 
            }
            
        # Apply correction to Comparison vs Control Family
        corrected_p_vals = _correct_p_values(vs_control_p_values, correction_method)
        
        for i, v_name in enumerate(vs_control_keys):
            p_corr = corrected_p_vals[i]
            results["variants"][v_name]["p_value_corrected"] = p_corr
            # Update significance based on corrected p-value? 
            # Usually significance is p_corr < alpha. Let's provide a specific flag.
            results["variants"][v_name]["is_significant_corrected"] = p_corr < 0.05

    # 3. All Pairwise Comparisons (Optional Extended Analysis)
    all_pairs_p_values: list[float] = []
    all_pairs_meta: list[dict[str, Any]] = []  # Stores pair comparison results
    
    # We need a predictable list of variant dicts
    # Convert df to list of dicts
    variant_list = []
    for _, row in df.iterrows():
        variant_list.append({
            "name": row["variant"],
            "users": int(row["users"]),
            "conversions": int(row["conversions"]),
            "rate": int(row["conversions"]) / int(row["users"]) if int(row["users"]) > 0 else 0.0
        })
        
    for var_a, var_b in itertools.combinations(variant_list, 2):
        # Calculate stats A vs B (diff = B - A usually, or directionless)
        # We'll treat var_a as baseline for 'lift' purposes directionally, but test is symmetric
        
        u_a, c_a, r_a = var_a["users"], var_a["conversions"], var_a["rate"]
        u_b, c_b, r_b = var_b["users"], var_b["conversions"], var_b["rate"]
        
        abs_lift = r_b - r_a
        
        p_val = 1.0
        if u_a > 0 and u_b > 0:
            try:
                counts = np.array([c_b, c_a])
                nobs = np.array([u_b, u_a])
                _, p_val_raw = proportions_ztest(count=counts, nobs=nobs, alternative='two-sided')
                p_val = float(p_val_raw)
            except Exception:
                pass
                
        all_pairs_p_values.append(float(p_val))
        all_pairs_meta.append({
            "variant_a": var_a["name"],
            "variant_b": var_b["name"],
            "absolute_lift": abs_lift,
            "p_value": p_val
        })
        
    # Apply correction to All Pairs Family
    all_pairs_corrected = _correct_p_values(all_pairs_p_values, correction_method)
    
    for i, meta in enumerate(all_pairs_meta):
        meta["p_value_corrected"] = all_pairs_corrected[i]
        meta["is_significant_corrected"] = all_pairs_corrected[i] < 0.05
        results["all_pairs"].append(meta)
        
    return results


def calculate_primary(df: pd.DataFrame) -> dict[str, Any]:
    """
    Primary Metric (전환율) 분석
    
    Args:
        df: 업로드된 데이터프레임 (variant, users, conversions 컬럼 필수)
    
    Returns:
        dict: {
            "control": {"users": int, "conversions": int, "rate": float},
            "treatment": {"users": int, "conversions": int, "rate": float},
            "absolute_lift": float,
            "relative_lift": float,
            "ci_95": [float, float],  # [lower, upper] absolute lift CI
            "p_value": float,
            "is_significant": bool
        }
    """
    # 데이터 추출
    control_row = df[df["variant"] == "control"].iloc[0]
    treatment_row = df[df["variant"] == "treatment"].iloc[0]
    
    users_c = int(control_row["users"])
    conv_c = int(control_row["conversions"])
    
    users_t = int(treatment_row["users"])
    conv_t = int(treatment_row["conversions"])
    
    # 1. 전환율 계산
    rate_c = conv_c / users_c if users_c > 0 else 0.0
    rate_t = conv_t / users_t if users_t > 0 else 0.0
    
    # 2. Lift 계산
    abs_lift = rate_t - rate_c
    
    # Relative lift: None if control rate is 0 to avoid inf/JSON issues
    if rate_c > 0:
        rel_lift = (rate_t / rate_c) - 1
    else:
        rel_lift = None  # Cannot compute meaningful relative lift from zero baseline
            
    # 3. 통계 검정 (Two-proportion z-test)
    # count: 성공 횟수 배열, nobs: 시행 횟수 배열
    counts = np.array([conv_t, conv_c])
    nobs = np.array([users_t, users_c])
    
    # 기본값 초기화
    p_value = 1.0
    ci_lower, ci_upper = 0.0, 0.0
    
    if users_c > 0 and users_t > 0:
        try:
            # 양측 검정 (alternative='two-sided')
            z_stat, p_value = proportions_ztest(count=counts, nobs=nobs, alternative='two-sided')
        except Exception as e:
            logger.warning(f"z-test 계산 실패: {e}")
            p_value = 1.0
            
        # 4. 95% 신뢰구간 (Absolute Lift)
        try:
            # method='wald' or 'agresti_caffo'
            ci_lower, ci_upper = confint_proportions_2indep(
                conv_t, users_t, 
                conv_c, users_c, 
                compare='diff', 
                alpha=0.05,
                method='agresti-caffo'
            )
        except Exception as e:
            logger.warning(f"CI 계산 실패: {e}")
            ci_lower, ci_upper = 0.0, 0.0
            
    is_significant = p_value < 0.05
    
    return {
        "control": {
            "users": users_c,
            "conversions": conv_c,
            "rate": rate_c
        },
        "treatment": {
            "users": users_t,
            "conversions": conv_t,
            "rate": rate_t
        },
        "absolute_lift": abs_lift,
        "relative_lift": rel_lift,
        "ci_95": [ci_lower, ci_upper],
        "p_value": p_value,
        "is_significant": is_significant
    }


def calculate_guardrails(
    df: pd.DataFrame,
    guardrail_columns: list[str] | None = None,
    abs_threshold: float = GUARDRAIL_WORSENED_THRESHOLD,
    severe_threshold: float = GUARDRAIL_SEVERE_THRESHOLD
) -> list[dict[str, Any]]:
    """
    Guardrail 분석
    
    Args:
        df: 업로드된 데이터프레임
        guardrail_columns: Guardrail 컬럼 리스트 (None이면 자동 탐지)
        abs_threshold: Worsened 판정 절대 임계치 (기본: 0.001 = 0.1%p)
        severe_threshold: Severe 판정 절대 임계치 (기본: 0.003 = 0.3%p)
    
    Returns:
        list of dict: [{
            "name": str,
            "control_count": int,
            "treatment_count": int,
            "control_rate": float,
            "treatment_rate": float,
            "delta": float,  # treatment_rate - control_rate
            "worsened": bool,
            "severe": bool,
            "p_value": float (선택)
        }, ...]
    """
    # Guardrail 컬럼 자동 탐지
    if guardrail_columns is None:
        required_cols = {"variant", "users", "conversions", "metric_sum", "metric_sum_sq", "n"}
        guardrail_columns = [
            col for col in df.columns 
            if col not in required_cols 
            and not col.endswith("_sum") 
            and not col.endswith("_sum_sq")
        ]
    
    if not guardrail_columns:
        return []
    
    control_row = df[df["variant"] == "control"].iloc[0]
    treatment_row = df[df["variant"] == "treatment"].iloc[0]
    
    users_c = int(control_row["users"])
    users_t = int(treatment_row["users"])
    
    results = []
    
    for col in guardrail_columns:
        try:
            count_c = int(control_row[col])
            count_t = int(treatment_row[col])
            
            # Rate 계산
            rate_c = count_c / users_c if users_c > 0 else 0.0
            rate_t = count_t / users_t if users_t > 0 else 0.0
            
            # Delta (Treatment - Control)
            delta = rate_t - rate_c
            
            # Worsened 판정 (delta >= abs_threshold)
            worsened = delta >= abs_threshold
            
            # Severe 판정
            severe = delta >= severe_threshold
            
            # (선택) P-value 계산
            try:
                counts = np.array([count_t, count_c])
                nobs = np.array([users_t, users_c])
                _, p_value = proportions_ztest(count=counts, nobs=nobs, alternative='two-sided')
            except (ValueError, ZeroDivisionError) as e:
                # Handle expected errors (e.g., zero users, invalid counts)
                logger.warning(f"P-value calculation failed for '{col}': {e}")
                p_value = 1.0
            
            # Relative lift: None if control rate is 0 (consistent with Primary)
            if rate_c > 0:
                rel_lift = (rate_t / rate_c) - 1
            else:
                rel_lift = None
            
            results.append({
                "name": col,
                "control_count": count_c,
                "treatment_count": count_t,
                "control_rate": rate_c,
                "treatment_rate": rate_t,
                "delta": delta,
                "relative_lift": rel_lift,  # Added for schema consistency
                "worsened": worsened,
                "severe": severe,
                "p_value": p_value
            })
        
        except (ValueError, TypeError, KeyError) as e:
            # Data structure or type errors - mark as error state
            logger.warning(f"Guardrail '{col}' 분석 실패 (데이터 오류): {e}")
            results.append({
                "name": col,
                "control_count": 0,
                "treatment_count": 0,
                "control_rate": 0.0,
                "treatment_rate": 0.0,
                "delta": 0.0,
                "relative_lift": None,  # Added for schema consistency
                "worsened": False,
                "severe": False,
                "p_value": 1.0,
                "error": str(e)
            })
        except Exception as e:
            # Unexpected errors - log and re-raise for visibility
            logger.error(f"Guardrail '{col}' 예상치 못한 오류: {e}")
            raise
    
    return results


def calculate_continuous_metrics(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Continuous Metric 분석 Orchestrator
    _sum, _sum_sq 컬럼을 탐지하여 분석 수행
    """
    results: list[dict[str, Any]] = []

    # Identify continuous metrics (look for _sum)
    metric_names = [
        col[:-4] for col in df.columns 
        if col.endswith("_sum") and col != "metric_sum"
    ]
    
    if not metric_names:
        return results
        
    control_row = df[df["variant"] == "control"].iloc[0]
    treatment_row = df[df["variant"] == "treatment"].iloc[0]
    
    for metric in metric_names:
        sum_col = f"{metric}_sum"
        sum_sq_col = f"{metric}_sum_sq"
        
        # Determine N (default to users)
        # In a fuller implementation, could look for {metric}_n or similar
        # For this MVP, we use 'users' as n (Revenue per User case)
        n_c = int(control_row["users"])
        n_t = int(treatment_row["users"])
        
        control_stats = {
            "sum": float(control_row[sum_col]),
            "sum_sq": float(control_row[sum_sq_col]),
            "n": n_c
        }
        
        treatment_stats = {
            "sum": float(treatment_row[sum_col]),
            "sum_sq": float(treatment_row[sum_sq_col]),
            "n": n_t
        }
        
        result = calculate_continuous_lift(control_stats, treatment_stats, metric)
        if result["is_valid"]:
            results.append(result)
            
    return results


def calculate_bayesian_insights(
    df: pd.DataFrame,
    continuous_results: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """
    Bayesian 분석 Orchestrator (Informational)
    """
    insights: dict[str, Any] = {
        "conversion": None,
        "continuous": {}
    }
    
    control_row = df[df["variant"] == "control"].iloc[0]
    treatment_row = df[df["variant"] == "treatment"].iloc[0]
    
    # 1. Conversion Rate (Beta-Binomial)
    try:
        insights["conversion"] = calculate_beta_binomial(
            control_conversions=int(control_row["conversions"]),
            control_total=int(control_row["users"]),
            treatment_conversions=int(treatment_row["conversions"]),
            treatment_total=int(treatment_row["users"])
        )
    except Exception as e:
        logger.warning(f"Bayesian conversion analysis failed: {e}")
        
    # 2. Continuous Metrics
    if continuous_results:
        for res in continuous_results:
            metric = res["metric_name"]
            try:
                # Reconstruct sufficient stats roughly from means/n (or pass them in if we wanted to be cleaner)
                # But here we assume 'n' matches 'users' as per calculate_continuous_metrics assumptions
                
                # Check for zero variance edge cases handled in continuous_analysis
                # If result was valid, we can compute Bayes
                
                # We need sum info again. Let's just grab from DF for simplicity.
                sum_col = f"{metric}_sum"
                sum_sq_col = f"{metric}_sum_sq"
                
                c_stats = {
                    "sum": float(control_row[sum_col]),
                    "sum_sq": float(control_row[sum_sq_col]),
                    "n": int(control_row["users"])
                }
                t_stats = {
                    "sum": float(treatment_row[sum_col]),
                    "sum_sq": float(treatment_row[sum_sq_col]),
                    "n": int(treatment_row["users"])
                }
                
                insights["continuous"][metric] = calculate_continuous_bayes(c_stats, t_stats)
            except Exception as e:
                logger.warning(f"Bayesian continuous analysis failed for {metric}: {e}")
                
    return insights

