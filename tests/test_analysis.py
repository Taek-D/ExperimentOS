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
        assert result["is_significant"] is True
        assert result["p_value"] < 0.05
        
        # CI 확인 (양수 범위여야 함)
        ci = result["ci_95"]
        assert ci[0] > 0
        assert ci[1] > 0
    
    def test_calculate_primary_not_significant(self):
        """유의한 차이가 없는 경우"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1010]  # 10% vs 10.1% (미미한 차이)
        })
        
        result = calculate_primary(df)
        
        # Rate 확인
        assert result["control"]["rate"] == 0.10
        assert result["treatment"]["rate"] == 0.101
        
        # 유의성 확인
        assert result["is_significant"] is False
        assert result["p_value"] >= 0.05
    
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
        # Relative lift는 inf 처리 (또는 아주 큰 값)
        assert result["relative_lift"] == float('inf')
        
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
        assert result["p_value"] == 1.0  # p-value 1.0 처리
        assert result["is_significant"] is False

    def test_calculate_primary_negative_lift(self):
        """Treatment가 더 나쁜 경우 (음수 Lift)"""
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1200, 1000]  # 12% vs 10%
        })
        
        result = calculate_primary(df)
        
        assert result["absolute_lift"] == -0.02
        assert result["relative_lift"] < 0
        assert result["is_significant"] is True  # 차이가 크므로 유의함
        
        # CI 확인 (음수 범위여야 함)
        ci = result["ci_95"]
        assert ci[0] < 0
        assert ci[1] < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
