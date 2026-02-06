"""
분석 모듈 단위 테스트
"""

import pytest
import pandas as pd
import numpy as np
from src.experimentos.analysis import calculate_primary


class TestCalculatePrimary:
    """Primary 분석 테스트"""
    
    def test_calculate_primary_significant(self):
        """유의한 차이가 있는 경우"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200]  # 10% vs 12%
        })
        
        result = calculate_primary(df)
        
        # Rate 확인
        assert result["control"]["rate"] == 0.10
        assert result["treatment"]["rate"] == 0.12
        
        # Lift 확인
        assert abs(result["absolute_lift"] - 0.02) < 1e-9
        assert abs(result["relative_lift"] - 0.20) < 1e-9
        
        # 유의성 확인
        assert result["is_significant"]
        assert result["p_value"] < 0.05
        
        # CI 확인 (양수 범위여야 함)
        ci = result["ci_95"]
        assert ci[0] > 0
        assert ci[1] > 0
    
    def test_calculate_primary_not_significant(self):
        """Test non-significant result"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1050]
        })
        result = calculate_primary(df)
        
        # Rate 확인
        assert result["control"]["rate"] == 0.10
        assert result["treatment"]["rate"] == 0.105
        
        # 유의성 확인
        assert not result["is_significant"]
        assert result["p_value"] > 0.05
    
    def test_calculate_primary_zero_conversions(self):
        """Control 전환율이 0인 경우"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [0, 100]
        })
        
        result = calculate_primary(df)
        
        assert result["control"]["rate"] == 0.0
        assert result["absolute_lift"] > 0
        # Relative lift는 None 처리 (control rate가 0이므로 의미 없음)
        assert result["relative_lift"] is None  # Fixed: was float('inf')
        
    def test_calculate_primary_zero_users(self):
        """Users가 0인 경우 (예외 방어)"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [0, 0],
            "conversions": [0, 0]
        })
    
        # ZeroDivisionError 없이 처리되어야 함
        result = calculate_primary(df)
        
        assert result["control"]["rate"] == 0.0
        assert result["treatment"]["rate"] == 0.0
        # Expect nan for p_value or handle it; original code might produce nan
        assert np.isnan(result["p_value"]) or result["p_value"] == 1.0
        assert not result["is_significant"]

    def test_calculate_primary_negative_lift(self):
        """Treatment가 더 나쁜 경우 (음수 Lift)"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1200, 1000]  # 12% vs 10%
        })
        
        result = calculate_primary(df)
        
        assert result["absolute_lift"] == pytest.approx(-0.02)
        assert result["relative_lift"] < 0
        assert result["is_significant"]  # 차이가 크므로 유의함
        
        # CI 확인 (음수 범위여야 함)
        ci = result["ci_95"]
        assert ci[0] < 0
        assert ci[1] < 0


class TestCalculateGuardrails:
    """Guardrail 분석 테스트 (Must-Fix #2)"""
    
    def test_guardrail_relative_lift_normal(self):
        """Guardrail relative_lift 정상 계산"""
        from src.experimentos.analysis import calculate_guardrails
        
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200],
            "bounce_rate": [500, 450]  # Guardrail metric: 5% → 4.5%
        })
        
        results = calculate_guardrails(df, ["bounce_rate"])
        
        assert len(results) == 1
        assert results[0]["name"] == "bounce_rate"
        assert results[0]["control_rate"] == 0.05
        assert results[0]["treatment_rate"] == 0.045
        # relative_lift = (0.045 / 0.05) - 1 = -0.1
        assert results[0]["relative_lift"] == pytest.approx(-0.1)
    
    def test_guardrail_relative_lift_zero_control(self):
        """Guardrail relative_lift - control rate가 0인 경우"""
        from src.experimentos.analysis import calculate_guardrails
        
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200],
            "bounce_rate": [0, 450]  # Control bounce_rate = 0
        })
        
        results = calculate_guardrails(df, ["bounce_rate"])
        
        assert len(results) == 1
        assert results[0]["control_rate"] == 0.0
        assert results[0]["treatment_rate"] == 0.045
        # relative_lift는 None (control rate가 0이므로 의미 없음)
        assert results[0]["relative_lift"] is None
    
    def test_guardrail_relative_lift_error_state(self):
        """Guardrail 에러 상태에서도 relative_lift 존재"""
        from src.experimentos.analysis import calculate_guardrails
        
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200],
            # bounce_rate 누락 - KeyError 발생 예상
        })
        
        results = calculate_guardrails(df, ["bounce_rate"])
        
        assert len(results) == 1
        assert "error" in results[0]
        # 에러 상태에서도 relative_lift는 None으로 스키마 일관성 유지
        assert results[0]["relative_lift"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

