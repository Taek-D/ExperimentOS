"""
Decision Framework 단위 테스트 (전체 분기 테스트)

make_decision() 함수의 6가지 결정 룰을 모두 테스트합니다.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.experimentos.memo import make_decision


class TestDecisionBranches:
    """Decision Framework의 모든 분기 테스트"""
    
    def test_rule1_blocked_schema(self):
        """룰 1: Blocked (스키마 오류) → Hold"""
        health = {
            "overall_status": "Blocked",
            "schema": {
                "status": "Blocked",
                "issues": ["필수 컬럼 누락: conversions"]
            },
            "srm": None
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "데이터 품질 문제" in result["reason"]
        assert "필수 컬럼 누락" in result["details"][0]
    
    def test_rule2_srm_warning(self):
        """룰 2: SRM Warning → Hold"""
        health = {
            "overall_status": "Warning",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {
                "status": "Warning",
                "p_value": 0.0005,
                "message": "SRM 경고 (p=0.0005)"
            }
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "SRM 탐지" in result["reason"]
        assert "0.0005" in result["reason"]
    
    def test_rule3_severe_guardrail_rollback(self):
        """룰 3: Primary 유의 + Severe Guardrail → Rollback"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01,
            "absolute_lift": 0.02
        }
        
        guardrails = [
            {
                "name": "error_rate",
                "delta": 0.005,  # 0.5%p (severe)
                "worsened": True,
                "severe": True
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Rollback"
        assert "심각한 Guardrail 악화" in result["reason"]
        assert "error_rate" in result["reason"]
    
    def test_rule4_worsened_guardrail_hold(self):
        """룰 4: Primary 유의 + Guardrail 악화 → Hold"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01,
            "absolute_lift": 0.02
        }
        
        guardrails = [
            {
                "name": "crash_rate",
                "delta": 0.0015,  # 0.15%p (worsened but not severe)
                "worsened": True,
                "severe": False
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "Guardrail 악화" in result["reason"]
        assert "crash_rate" in result["reason"]
    
    def test_rule5_launch_significant_no_guardrail_issues(self):
        """룰 5: Primary 유의 + Guardrail 정상 → Launch"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01,
            "absolute_lift": 0.02,
            "relative_lift": 0.15,
            "ci_95": [0.01, 0.03]
        }
        
        guardrails = [
            {
                "name": "error_rate",
                "delta": 0.0005,  # 0.05%p (OK)
                "worsened": False,
                "severe": False
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Launch"
        assert "Primary 유의" in result["reason"]
        assert "Guardrail 정상" in result["reason"]
    
    def test_rule6_hold_not_significant(self):
        """룰 6: Primary 비유의 → Hold"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": False,
            "p_value": 0.25,
            "absolute_lift": 0.005
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "Primary 비유의" in result["reason"]
        assert "0.25" in result["reason"]
    
    def test_multiple_guardrails_prioritize_severe(self):
        """여러 Guardrail 중 Severe가 우선"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01
        }
        
        guardrails = [
            {
                "name": "error_rate",
                "delta": 0.0015,
                "worsened": True,
                "severe": False
            },
            {
                "name": "crash_rate",
                "delta": 0.004,
                "worsened": True,
                "severe": True
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        # Severe가 있으면 Rollback
        assert result["decision"] == "Rollback"
        assert "crash_rate" in result["reason"]
    
    def test_srm_blocked_overrides_significant_primary(self):
        """SRM Blocked는 Primary 유의보다 우선"""
        health = {
            "overall_status": "Blocked",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {
                "status": "Blocked",
                "p_value": 0.000001,
                "message": "심각한 SRM"
            }
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.001,
            "absolute_lift": 0.05
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        # Primary가 유의해도 SRM Blocked면 Hold
        assert result["decision"] == "Hold"
        assert "Blocked" in result["reason"]


class TestDecisionEdgeCases:
    """Decision Framework의 Edge Cases"""
    
    def test_empty_guardrails_list(self):
        """Guardrail이 없는 경우"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.8}
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01,
            "absolute_lift": 0.02,
            "relative_lift": 0.15,
            "ci_95": [0.01, 0.03]
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        # Guardrail 없어도 Launch 가능
        assert result["decision"] == "Launch"
    
    def test_no_srm_data(self):
        """SRM 데이터가 None인 경우"""
        health = {
            "overall_status": "Warning",
            "schema": {
                "status": "Warning",
                "issues": ["작은 표본"]
            },
            "srm": None  # SRM 검증 스킵됨
        }
        
        primary = {
            "is_significant": True,
            "p_value": 0.01,
            "absolute_lift": 0.02,
            "relative_lift": 0.15,
            "ci_95": [0.01, 0.03]
        }
        
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        # SRM이 None이어도 Launch 가능 (Warning은 허용)
        assert result["decision"] == "Launch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
