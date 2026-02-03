"""
Health Check 모듈

CSV 데이터의 스키마 검증 및 SRM(Sample Ratio Mismatch) 탐지
"""

import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging

from .config import SRM_WARNING_THRESHOLD, SRM_BLOCKED_THRESHOLD, MIN_SAMPLE_SIZE_WARNING, config

logger = logging.getLogger("experimentos")


def validate_schema(df: pd.DataFrame) -> Dict:
    """
    CSV 데이터의 스키마 및 논리적 오류를 검증
    
    Args:
        df: 업로드된 데이터프레임
    
    Returns:
        dict: {
            "status": "Healthy" | "Warning" | "Blocked",
            "issues": List[str]  # 발견된 이슈 목록
        }
    """
    issues = []
    
    # 1. 필수 컬럼 체크
    required_columns = ["variant", "users", "conversions"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        issues.append(f"필수 컬럼 누락: {', '.join(missing_columns)}")
        return {"status": "Blocked", "issues": issues}
    
    # 2. variant 라벨 검증
    variants = df["variant"].str.strip().str.lower().unique()
    
    if len(df) != 2:
        issues.append(f"데이터는 정확히 2개 행이어야 합니다 (현재: {len(df)}행)")
        return {"status": "Blocked", "issues": issues}

    if len(variants) != 2:
        issues.append(f"variant는 정확히 2개여야 합니다 (현재: {len(variants)}개)")
        return {"status": "Blocked", "issues": issues}
    
    if "control" not in variants or "treatment" not in variants:
        issues.append(f"variant는 'control'과 'treatment'여야 합니다 (현재: {', '.join(variants)})")
        return {"status": "Blocked", "issues": issues}
    
    # variant 정규화 (소문자, 공백 제거)
    df["variant"] = df["variant"].str.strip().str.lower()
    
    # 3. 타입 검증
    try:
        df["users"] = pd.to_numeric(df["users"], errors="raise")
        df["conversions"] = pd.to_numeric(df["conversions"], errors="raise")
    except (ValueError, TypeError) as e:
        issues.append(f"users 또는 conversions가 숫자가 아닙니다: {str(e)}")
        return {"status": "Blocked", "issues": issues}
    
    # 4. 음수 검증
    if (df["users"] < 0).any():
        issues.append("users에 음수 값이 있습니다")
        return {"status": "Blocked", "issues": issues}
    
    if (df["conversions"] < 0).any():
        issues.append("conversions에 음수 값이 있습니다")
        return {"status": "Blocked", "issues": issues}
    
    # 5. users > 0 검증
    if (df["users"] == 0).any():
        issues.append("users가 0인 행이 있습니다")
        return {"status": "Blocked", "issues": issues}
    
    # 6. conversions <= users 검증
    invalid_rows = df[df["conversions"] > df["users"]]
    if not invalid_rows.empty:
        issues.append(f"conversions가 users보다 큰 행이 있습니다 (variant: {', '.join(invalid_rows['variant'].tolist())})")
        return {"status": "Blocked", "issues": issues}
    
    # 7. NaN/NULL 검증
    if df[required_columns].isnull().any().any():
        issues.append("필수 컬럼에 NULL 값이 있습니다")
        return {"status": "Blocked", "issues": issues}
    
    # 8. 작은 표본 경고 (선택 사항)
    if (df["users"] < MIN_SAMPLE_SIZE_WARNING).any():
        issues.append(f"⚠️ Warning: users가 {MIN_SAMPLE_SIZE_WARNING} 미만인 행이 있습니다. 통계적 신뢰도가 낮을 수 있습니다.")
    
    # 9. Continuous Metric Schema Validation
    continuous_issues = validate_continuous_schema(df, issues)
    # validate_continuous_schema mutates issues, so we don't need to append return value if it's already in place
    # checking logic below handles the status
    
    # Check if any continuous validation added a Blocked issue
    if any("필수 컬럼 누락" in i or "불일치" in i or "Invalid variance" in i or "Continuous schema error" in i or "contains NULL" in i for i in issues):
         return {"status": "Blocked", "issues": issues}

    # If no blocked issues, check for warnings
    if any("Warning" in i for i in issues):
        return {"status": "Warning", "issues": issues}

    # 모든 검증 통과
    return {"status": "Healthy", "issues": issues if issues else ["검증 통과"]}


def validate_continuous_schema(df: pd.DataFrame, issues: List[str]) -> List[str]:
    """
    Continuous metric columns (_sum, _sum_sq) validation.
    Mutates 'issues' list if problems are found.
    """
    # 1. Identify sum columns
    sum_cols = [c for c in df.columns if c.endswith("_sum") and c != "metric_sum"]
    
    for sum_col in sum_cols:
        base_name = sum_col[:-4] # remove _sum
        sum_sq_col = f"{base_name}_sum_sq"
        
        # Check sum_sq existence
        if sum_sq_col not in df.columns:
            issues.append(f"Continuous schema error: '{sum_col}' exists but '{sum_sq_col}' is missing.")
            continue
            
        # Check completeness (values present for both variants)
        # Assuming df has 2 rows (control, treatment)
        if df[sum_col].isnull().any() or df[sum_sq_col].isnull().any():
             issues.append(f"Continuous metric '{base_name}' contains NULL values.")
             continue
             
        # Variance Feasibility Check
        # sum_sq >= (sum^2)/n
        for _, row in df.iterrows():
            n = row["users"] # Default n=users. (For AOV, might need 'orders' column, simplified for MVP)
            
            if n < 2:
                 # Cannot compute variance if n < 2 (though technically maybe valid data, for analysis it's useless)
                 # We skip strict blocking for n<2 unless it breaks something else, but let's warn.
                 continue

            s = row[sum_col]
            ss = row[sum_sq_col]
            
            # Variance feasibility: ss - s^2/n >= -tolerance
            implied_ss = ss - (s**2 / n)
            
            if implied_ss < -config.VAR_TOLERANCE:
                issues.append(f"Invalid variance for '{base_name}' in {row['variant']}: sum_sq < sum^2/n (diff={implied_ss:.2e})")

    return issues



def detect_srm(
    control_users: int,
    treatment_users: int,
    expected_split: Tuple[float, float] = (50.0, 50.0),
    warning_threshold: float = SRM_WARNING_THRESHOLD,
    blocked_threshold: float = SRM_BLOCKED_THRESHOLD
) -> Dict:
    """
    SRM (Sample Ratio Mismatch) 탐지
    
    Chi-square goodness-of-fit test를 사용하여 관측된 트래픽 분배가
    기대 분배와 유의하게 다른지 검증
    
    Args:
        control_users: Control variant 유저 수
        treatment_users: Treatment variant 유저 수
        expected_split: 기대 트래픽 분배 (control%, treatment%)
        warning_threshold: Warning 임계값 (기본: 0.001)
        blocked_threshold: Blocked 임계값 (기본: 0.00001)
    
    Returns:
        dict: {
            "status": "Healthy" | "Warning" | "Blocked",
            "p_value": float,
            "observed": {"control": int, "treatment": int},
            "expected": {"control": float, "treatment": float},
            "message": str
        }
    """
    total_users = control_users + treatment_users
    
    # Edge case: Zero users
    if total_users == 0:
        return {
            "status": "Blocked",
            "p_value": 1.0,
            "chi2_stat": 0.0,
            "observed": {
                "control": 0,
                "treatment": 0,
                "control_pct": 0.0,
                "treatment_pct": 0.0
            },
            "expected": {
                "control": 0.0,
                "treatment": 0.0,
                "control_pct": 0.0,
                "treatment_pct": 0.0
            },
            "message": "총 유저 수가 0입니다. SRM 탐지 불가능."
        }
    
    # 기대 비율 정규화
    expected_control_pct = expected_split[0] / sum(expected_split)
    expected_treatment_pct = expected_split[1] / sum(expected_split)
    
    # 기대값 계산
    expected_control = total_users * expected_control_pct
    expected_treatment = total_users * expected_treatment_pct
    
    # 관측값
    observed = [control_users, treatment_users]
    expected = [expected_control, expected_treatment]
    
    # Chi-square goodness-of-fit test
    chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
    
    # 상태 판정
    if p_value < blocked_threshold:
        status = "Blocked"
        message = f"심각한 SRM 탐지 (p={p_value:.2e}). 실험 데이터를 검토하세요."
    elif p_value < warning_threshold:
        status = "Warning"
        message = f"SRM 경고 (p={p_value:.4f}). 트래픽 분배를 확인하세요."
    else:
        status = "Healthy"
        message = f"SRM 정상 (p={p_value:.4f})"
    
    return {
        "status": status,
        "p_value": p_value,
        "chi2_stat": chi2_stat,
        "observed": {
            "control": control_users,
            "treatment": treatment_users,
            "control_pct": control_users / total_users * 100,
            "treatment_pct": treatment_users / total_users * 100
        },
        "expected": {
            "control": expected_control,
            "treatment": expected_treatment,
            "control_pct": expected_control_pct * 100,
            "treatment_pct": expected_treatment_pct * 100
        },
        "message": message
    }


def run_health_check(
    df: pd.DataFrame,
    expected_split: Tuple[float, float] = (50.0, 50.0)
) -> Dict:
    """
    전체 Health Check 실행 (스키마 검증 + SRM 탐지)
    
    Args:
        df: 업로드된 데이터프레임
        expected_split: 기대 트래픽 분배 (기본: 50/50)
    
    Returns:
        dict: {
            "schema": {...},  # validate_schema 결과
            "srm": {...},     # detect_srm 결과 (schema가 Healthy일 때만)
            "overall_status": "Healthy" | "Warning" | "Blocked"
        }
    """
    # 1. 스키마 검증
    schema_result = validate_schema(df.copy())
    
    result = {
        "schema": schema_result,
        "srm": None,
        "overall_status": schema_result["status"]
    }
    
    # 스키마가 Blocked면 SRM 검증 스킵
    if schema_result["status"] == "Blocked":
        return result
    
    # 2. SRM 탐지
    try:
        control_row = df[df["variant"] == "control"].iloc[0]
        treatment_row = df[df["variant"] == "treatment"].iloc[0]
        
        srm_result = detect_srm(
            control_users=int(control_row["users"]),
            treatment_users=int(treatment_row["users"]),
            expected_split=expected_split
        )
        
        result["srm"] = srm_result
        
        # 전체 상태 결정 (더 심각한 쪽 우선)
        if srm_result["status"] == "Blocked":
            result["overall_status"] = "Blocked"
        elif srm_result["status"] == "Warning" or schema_result["status"] == "Warning":
            result["overall_status"] = "Warning"
        else:
            result["overall_status"] = "Healthy"
    
    except Exception as e:
        logger.error(f"SRM 탐지 중 오류: {e}")
        result["srm"] = {
            "status": "Blocked",
            "message": f"SRM 탐지 실패: {str(e)}"
        }
        result["overall_status"] = "Blocked"
    
    return result
