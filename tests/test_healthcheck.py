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
        assert any("정확히 2개 행" in issue for issue in result["issues"])

    def test_srm_warning(self):
        """중간 정도의 SRM - Warning"""
        # 5000 vs 5400 (Total 10400, expected 5200)
        # ChiSq approx 15.38 -> p < 0.001 but > 0.00001
        result = detect_srm(
            control_users=5000,
            treatment_users=5400,
            expected_split=(50, 50)
        )
        
        assert result["status"] == "Warning"
        assert result["p_value"] < 0.001
        assert result["p_value"] >= 0.00001
    
    def test_srm_warning_overall_warning(self):
        """SRM Warning 시 전체 Warning"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [5000, 5400],
            "conversions": [600, 650]
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
