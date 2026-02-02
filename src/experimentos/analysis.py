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
    
    try:
        # 양측 검정 (alternative='two-sided')
        z_stat, p_value = proportions_ztest(count=counts, nobs=nobs, alternative='two-sided')
    except Exception as e:
        logger.warning(f"z-test 계산 실패: {e}")
        p_value = 1.0
        z_stat = 0.0
        
    # 4. 95% 신뢰구간 (Absolute Lift)
    try:
        # method='wald' or 'agresti_caffo' (여기서는 statsmodels 기본값 사용 고려, 
        # confint_proportions_2indep의 기본값은 'agresti-caffo'가 됨)
        # compare='diff' -> p1 - p2 (Treatment - Control)
        # alpha=0.05 -> 95% CI
        
        # 주의: statsmodels 함수 인자 순서 (count1, nobs1, count2, nobs2)
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
        required_cols = {"variant", "users", "conversions"}
        guardrail_columns = [col for col in df.columns if col not in required_cols]
    
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
