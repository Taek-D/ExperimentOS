"""
Health Check 모듈 단위 테스트
"""

import pytest
import pandas as pd
from src.experimentos.healthcheck import validate_schema, detect_srm, run_health_check


class TestValidateSchema:
    """스키마 검증 테스트"""
    
    def test_valid_schema(self):
        """정상 데이터 - Healthy"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1200, 1320]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Healthy"
        assert "검증 통과" in result["issues"]
    
    def test_missing_column(self):
        """필수 컬럼 누락 - Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000]
            # conversions 누락
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("필수 컬럼 누락" in issue for issue in result["issues"])
    
    def test_conversions_exceeds_users(self):
        """conversions > users - Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [12000, 1320]  # control의 conversions가 users보다 큼
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("conversions가 users보다 큰" in issue for issue in result["issues"])
    
    def test_negative_values(self):
        """음수 값 - Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [-100, 10000],
            "conversions": [1200, 1320]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("음수" in issue for issue in result["issues"])
    
    def test_invalid_variant_labels(self):
        """잘못된 variant 라벨 - Blocked"""
        df = pd.DataFrame({
            "variant": ["A", "B"],
            "users": [10000, 10000],
            "conversions": [1200, 1320]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("control" in issue and "treatment" in issue for issue in result["issues"])
    
    def test_duplicate_variants(self):
        """variant 중복 - Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "control", "treatment"],
            "users": [5000, 5000, 10000],
            "conversions": [600, 600, 1320]
        })
        
        result = validate_schema(df)
        
        # variant가 3개이므로 Blocked
        assert result["status"] == "Blocked"
    
    def test_zero_users(self):
        """users가 0 - Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [0, 10000],
            "conversions": [0, 1320]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("0인 행" in issue for issue in result["issues"])
    
    def test_small_sample_warning(self):
        """작은 표본 - Warning"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [50, 50],
            "conversions": [5, 7]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Warning"
        assert any("100 미만" in issue for issue in result["issues"])
    
    def test_variant_case_insensitive(self):
        """variant 대소문자 무시 - Healthy"""
        df = pd.DataFrame({
            "variant": ["Control", "TREATMENT"],
            "users": [10000, 10000],
            "conversions": [1200, 1320]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Healthy"


class TestDetectSRM:
    """SRM 탐지 테스트"""
    
    def test_no_srm_50_50(self):
        """SRM 없음 (50/50 split) - Healthy"""
        result = detect_srm(
            control_users=10000,
            treatment_users=10000,
            expected_split=(50, 50)
        )
        
        assert result["status"] == "Healthy"
        assert result["p_value"] > 0.05
    
    def test_slight_imbalance_healthy(self):
        """약간의 불균형 (통계적으로 유의하지 않음) - Healthy"""
        result = detect_srm(
            control_users=10000,
            treatment_users=10100,
            expected_split=(50, 50)
        )
        
        assert result["status"] == "Healthy"
    
    def test_srm_warning(self):
        """중간 정도의 SRM - Warning"""
        result = detect_srm(
            control_users=5000,
            treatment_users=7000,
            expected_split=(50, 50)
        )
        
        assert result["status"] == "Warning"
        assert result["p_value"] < 0.001
        assert result["p_value"] >= 0.00001
    
    def test_srm_blocked(self):
        """심각한 SRM - Blocked"""
        result = detect_srm(
            control_users=5000,
            treatment_users=10000,
            expected_split=(50, 50)
        )
        
        assert result["status"] == "Blocked"
        assert result["p_value"] < 0.00001
    
    def test_custom_split_60_40(self):
        """커스텀 split (60/40) - Healthy"""
        result = detect_srm(
            control_users=6000,
            treatment_users=4000,
            expected_split=(60, 40)
        )
        
        assert result["status"] == "Healthy"
        assert result["p_value"] > 0.05
    
    def test_custom_split_violation(self):
        """커스텀 split 위반 - Warning/Blocked"""
        result = detect_srm(
            control_users=5000,
            treatment_users=5000,
            expected_split=(60, 40)  # 50/50인데 60/40 기대
        )
        
        # 50/50는 60/40과 차이가 크므로 Warning 이상
        assert result["status"] in ["Warning", "Blocked"]


class TestRunHealthCheck:
    """통합 Health Check 테스트"""
    
    def test_healthy_data(self):
        """정상 데이터 - 전체 Healthy"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1200, 1320]
        })
        
        result = run_health_check(df, expected_split=(50, 50))
        
        assert result["overall_status"] == "Healthy"
        assert result["schema"]["status"] == "Healthy"
        assert result["srm"]["status"] == "Healthy"
    
    def test_schema_blocked_skips_srm(self):
        """스키마 Blocked 시 SRM 스킵"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [12000, 1320]  # conversions > users
        })
        
        result = run_health_check(df)
        
        assert result["overall_status"] == "Blocked"
        assert result["schema"]["status"] == "Blocked"
        assert result["srm"] is None  # SRM 검증 스킵
    
    def test_srm_warning_overall_warning(self):
        """SRM Warning 시 전체 Warning"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [5000, 7000],
            "conversions": [600, 910]
        })
        
        result = run_health_check(df, expected_split=(50, 50))
        
        assert result["overall_status"] == "Warning"
        assert result["srm"]["status"] == "Warning"
    
    def test_srm_blocked_overall_blocked(self):
        """SRM Blocked 시 전체 Blocked"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [5000, 10000],
            "conversions": [600, 1300]
        })
        
        result = run_health_check(df, expected_split=(50, 50))
        
        assert result["overall_status"] == "Blocked"
        assert result["srm"]["status"] == "Blocked"


# 테스트 실행 코드 (pytest로 실행 시 자동)
def test_srm_zero_users():
    """SRM detection with 0 total users should return Blocked."""
    result = detect_srm(
        control_users=0,
        treatment_users=0,
        expected_split=(50, 50)
    )
    
    assert result["status"] == "Blocked"
    assert result["p_value"] == 1.0
    assert "0" in result["message"] or "유저" in result["message"]


def test_srm_very_small_users():
    """SRM with very small users should still calculate."""
    result = detect_srm(
        control_users=5,
        treatment_users=5,
        expected_split=(50, 50)
    )
    
    assert result["status"] in ["Healthy", "Warning", "Blocked"]
    assert result["p_value"] >= 0.0
    assert result["p_value"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
