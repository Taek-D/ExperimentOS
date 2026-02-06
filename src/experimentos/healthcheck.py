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
    
    if len(df) < 2:
        issues.append(f"데이터는 최소 2개 행이어야 합니다 (현재: {len(df)}행)")
        return {"status": "Blocked", "issues": issues}

    if len(variants) < 2:
        issues.append(f"variant는 최소 2개여야 합니다 (현재: {len(variants)}개)")
        return {"status": "Blocked", "issues": issues}
    
    if "control" not in variants:
        issues.append(f"variant에 'control' 그룹이 반드시 포함되어야 합니다 (현재: {', '.join(variants)})")
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
    
    # Check for duplicates
    if df["variant"].duplicated().any():
        issues.append("중복된 variant 라벨이 있습니다.")
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
    continuous_status = validate_continuous_schema(df, issues)
    
    # Check continuous validation status (simplified from keyword search)
    if continuous_status == "Blocked":
        return {"status": "Blocked", "issues": issues}

    # If no blocked issues, check for warnings
    if continuous_status == "Warning" or any("Warning" in i for i in issues):
        return {"status": "Warning", "issues": issues}

    # 모든 검증 통과
    return {"status": "Healthy", "issues": issues if issues else ["검증 통과"]}


def validate_continuous_schema(df: pd.DataFrame, issues: List[str]) -> str:
    """
    Continuous metric columns (_sum, _sum_sq) validation.
    Mutates 'issues' list if problems are found.
    
    Returns:
        str: Validation status indicating the severity of issues found
            - "Healthy": All continuous metrics are valid with no issues
            - "Warning": Non-blocking issues found (e.g., n<2 preventing variance calculation)
            - "Blocked": Critical issues found that prevent analysis
                * Missing _sum_sq column for existing _sum column
                * NULL values in continuous metric columns
                * Invalid variance (sum_sq < sum^2/n beyond tolerance)
    
    Priority Order:
        1. Blocked (highest) - Critical issues that prevent analysis
        2. Warning (medium) - Non-critical issues that may affect reliability
        3. Healthy (lowest) - No issues found
    
    Note:
        This function mutates the 'issues' list by appending error messages.
        The caller should check both the return status and the issues list
        for complete validation results.
    
    Examples:
        >>> issues = []
        >>> status = validate_continuous_schema(df, issues)
        >>> if status == "Blocked":
        >>>     print(f"Cannot proceed: {issues}")
    """
    has_blocked_issue = False
    has_warning_issue = False
    
    # 1. Identify sum columns
    sum_cols = [c for c in df.columns if c.endswith("_sum") and c != "metric_sum"]
    
    for sum_col in sum_cols:
        base_name = sum_col[:-4] # remove _sum
        sum_sq_col = f"{base_name}_sum_sq"
        
        # Check sum_sq existence
        if sum_sq_col not in df.columns:
            issues.append(f"Continuous schema error: '{sum_col}' exists but '{sum_sq_col}' is missing.")
            has_blocked_issue = True
            continue
            
        # Check completeness (values present for both variants)
        # Assuming df has 2 rows (control, treatment)
        if df[sum_col].isnull().any() or df[sum_sq_col].isnull().any():
             issues.append(f"Continuous metric '{base_name}' contains NULL values.")
             has_blocked_issue = True
             continue
             
        # Variance Feasibility Check
        # sum_sq >= (sum^2)/n
        for _, row in df.iterrows():
            n = row["users"] # Default n=users. (For AOV, might need 'orders' column, simplified for MVP)
            
            if n < 2:
                 # Cannot compute variance if n < 2
                 issues.append(f"⚠️ Warning: Continuous metric '{base_name}' has n={n} for {row['variant']}. Variance requires n≥2.")
                 has_warning_issue = True
                 continue

            s = row[sum_col]
            ss = row[sum_sq_col]
            
            # Variance feasibility: ss - s^2/n >= -tolerance
            implied_ss = ss - (s**2 / n)
            
            if implied_ss < -config.VAR_TOLERANCE:
                issues.append(f"Invalid variance for '{base_name}' in {row['variant']}: sum_sq < sum^2/n (diff={implied_ss:.2e})")
                has_blocked_issue = True

    # Return explicit status with clear priority
    # Priority: Blocked > Warning > Healthy
    # If both Blocked and Warning issues exist, Blocked takes precedence
    if has_blocked_issue:
        return "Blocked"  # Highest priority - prevents analysis
    elif has_warning_issue:
        return "Warning"  # Medium priority - may affect reliability
    else:
        return "Healthy"  # Lowest priority - no issues found



def detect_srm(
    variants_data: Dict[str, int],
    expected_split: Optional[List[float]] = None,
    warning_threshold: float = SRM_WARNING_THRESHOLD,
    blocked_threshold: float = SRM_BLOCKED_THRESHOLD
) -> Dict:
    """
    SRM (Sample Ratio Mismatch) 탐지 (N-variant 지원)
    
    Chi-square goodness-of-fit test를 사용하여 관측된 트래픽 분배가
    기대 분배와 유의하게 다른지 검증
    
    Args:
        variants_data: {variant_name: user_count} 딕셔너리
        expected_split: 기대 트래픽 분배 리스트 (예: [50, 50] 또는 [33.3, 33.3, 33.3]). 
                        None인 경우 균등 분배로 가정.
                        순서는 variants_data 키의 알파벳/정렬 순서 또는 입력 순서에 따름 (여기서는 variants_data.keys() 순서)
        warning_threshold: Warning 임계값
        blocked_threshold: Blocked 임계값
    
    Returns:
        dict: {
            "status": "Healthy" | "Warning" | "Blocked",
            "p_value": float,
            "observed": Dict[str, int],
            "expected": Dict[str, float],
            "message": str
        }
    """
    variant_names = list(variants_data.keys())
    observed = [variants_data[v] for v in variant_names]
    total_users = sum(observed)
    num_variants = len(observed)
    
    # Init structure
    observed_dict = {}
    expected_dict = {}
    
    # 0. Edge cases
    if num_variants < 2:
        return {
            "status": "Warning",
            "message": "비교할 variant가 부족하여 SRM 탐지를 건너뜁니다."
        }

    if total_users == 0:
        return {
            "status": "Warning",
            "p_value": 1.0,
            "chi2_stat": 0.0,
            "observed": {v: 0 for v in variant_names},
            "expected": {v: 0.0 for v in variant_names},
            "message": "총 유저 수가 0입니다. 데이터가 없어 SRM 탐지가 불가능합니다."
        }
    
    # 1. Expected Split 설정
    if expected_split is None or len(expected_split) != num_variants:
        # Default to equal split if not provided or size mismatch
        # e.g., 2 variants -> [0.5, 0.5], 3 -> [0.33, 0.33, 0.33]
        equal_share = 1.0 / num_variants
        expected_probs = [equal_share] * num_variants
    else:
        total_expected = sum(expected_split)
        if total_expected <= 0:
             # Fallback to equal
             expected_probs = [1.0 / num_variants] * num_variants
        else:
             expected_probs = [x / total_expected for x in expected_split]
    
    expected_counts = [total_users * p for p in expected_probs]

    # 2. Chi-square test
    chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected_counts)
    
    # 3. Build Result Dicts
    for i, v_name in enumerate(variant_names):
        observed_dict[v_name] = observed[i]
        expected_dict[v_name] = expected_counts[i]
        # Calculate percentages for info
        observed_dict[f"{v_name}_pct"] = (observed[i] / total_users) * 100  # type: ignore[assignment]
        expected_dict[f"{v_name}_pct"] = expected_probs[i] * 100

    # 4. Status Check
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
        "observed": observed_dict,
        "expected": expected_dict,
        "message": message
    }


def run_health_check(
    df: pd.DataFrame,
    expected_split: Optional[List[float]] = None
) -> Dict:
    """
    전체 Health Check 실행 (스키마 검증 + SRM 탐지)
    
    Args:
        df: 업로드된 데이터프레임
        expected_split: 기대 트래픽 분배 리스트 (기본: None -> Equal Split)
                        2개일 경우 (50, 50) 등.
    
    Returns:
        dict: {
            "schema": {...},
            "srm": {...},
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
    
    # 2. SRM 탐지 준비
    try:
        # Extract users per variant
        # Ensure correct order logic or pass as dict
        # Assuming df has unique variants (checked in schema)
        variants_map = dict(zip(df["variant"], df["users"]))
        
        # If expected_split provided, ensure we map it correctly.
        # But for generic purpose, simplest is assuming df order/map matches expected_split order if provided list.
        # Better: if expected_split is provided, document that it must match alpha-sorted variants or Input order.
        # Here we use the order from DF iteration which is consistent with read order.

        srm_result = detect_srm(
            variants_data=variants_map,
            expected_split=expected_split
        )
        
        result["srm"] = srm_result
        
        # 전체 상태 결정 (더 심각한 쪽 우선)
        if srm_result.get("status") == "Blocked":
            result["overall_status"] = "Blocked"
        elif srm_result.get("status") == "Warning" or schema_result["status"] == "Warning":
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
