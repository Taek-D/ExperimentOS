"""
분석 모듈

Primary metric(전환율) 및 Guardrail 분석 로직
"""

import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
from typing import Dict, List, Optional, Tuple
import logging

from .config import GUARDRAIL_WORSENED_THRESHOLD, GUARDRAIL_SEVERE_THRESHOLD
from .continuous_analysis import calculate_continuous_lift
from .bayesian import calculate_beta_binomial, calculate_continuous_bayes

logger = logging.getLogger("experimentos")


def calculate_primary(df: pd.DataFrame) -> Dict:
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
    
    if rate_c > 0:
        rel_lift = (rate_t / rate_c) - 1
    else:
        # Control 전환율이 0인 경우
        if rate_t > 0:
            rel_lift = float('inf')
        else:
            rel_lift = 0.0
            
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
    guardrail_columns: Optional[List[str]] = None,
    abs_threshold: float = GUARDRAIL_WORSENED_THRESHOLD,
    severe_threshold: float = GUARDRAIL_SEVERE_THRESHOLD
) -> List[Dict]:
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
            except:
                p_value = 1.0
            
            results.append({
                "name": col,
                "control_count": count_c,
                "treatment_count": count_t,
                "control_rate": rate_c,
                "treatment_rate": rate_t,
                "delta": delta,
                "worsened": worsened,
                "severe": severe,
                "p_value": p_value
            })
        
        except Exception as e:
            logger.warning(f"Guardrail '{col}' 분석 실패: {e}")
            continue
    
    return results


def calculate_continuous_metrics(df: pd.DataFrame) -> List[Dict]:
    """
    Continuous Metric 분석 Orchestrator
    _sum, _sum_sq 컬럼을 탐지하여 분석 수행
    """
    results = []
    
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
    continuous_results: List[Dict] = None
) -> Dict:
    """
    Bayesian 분석 Orchestrator (Informational)
    """
    insights = {
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

