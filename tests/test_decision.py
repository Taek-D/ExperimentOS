"""
Decision Framework 단위 테스트
"""

import pytest
from src.experimentos.memo import make_decision


class TestMakeDecision:
    """Decision Framework 테스트"""
    
    def test_decision_blocked_schema(self):
        """스키마 Blocked → Hold"""
        health = {
            "overall_status": "Blocked",
            "schema": {"status": "Blocked", "issues": ["필수 컬럼 누락"]},
            "srm": None
        }
        primary = {"is_significant": True, "p_value": 0.001}
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "Blocked" in result["reason"]
    
    def test_decision_srm_warning(self):
        """SRM Warning → Hold"""
        health = {
            "overall_status": "Warning",
            "schema": {"status": "Healthy", "issues": []},
            "srm": {"status": "Warning", "p_value": 0.0005, "message": "SRM 경고"}
        }
        primary = {"is_significant": True, "p_value": 0.001}
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "SRM" in result["reason"]
    
    def test_decision_severe_guardrail(self):
        """Primary 유의 + Severe Guardrail → Rollback"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": []},
            "srm": {"status": "Healthy", "p_value": 0.9}
        }
        primary = {"is_significant": True, "p_value": 0.001, "absolute_lift": 0.02, "relative_lift": 0.2, "ci_95": [0.01, 0.03]}
        guardrails = [
            {"name": "error_rate", "delta": 0.004, "worsened": True, "severe": True}
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Rollback"
        assert "error_rate" in result["reason"]
    
    def test_decision_worsened_guardrail(self):
        """Primary 유의 + Worsened Guardrail → Hold"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": []},
            "srm": {"status": "Healthy", "p_value": 0.9}
        }
        primary = {"is_significant": True, "p_value": 0.001, "absolute_lift": 0.02, "relative_lift": 0.2, "ci_95": [0.01, 0.03]}
        guardrails = [
            {"name": "cancel_rate", "delta": 0.002, "worsened": True, "severe": False}
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "cancel_rate" in result["reason"]
    
    def test_decision_launch(self):
        """Primary 유의 + Guardrail 정상 → Launch"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": []},
            "srm": {"status": "Healthy", "p_value": 0.9}
        }
        primary = {
            "is_significant": True,
            "p_value": 0.001,
            "absolute_lift": 0.02,
            "relative_lift": 0.2,
            "ci_95": [0.01, 0.03]
        }
        guardrails = [
            {"name": "error_rate", "delta": 0.0001, "worsened": False, "severe": False}
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Launch"
        assert "유의" in result["reason"] and "정상" in result["reason"]
    
    def test_decision_not_significant(self):
        """Primary 비유의 → Hold"""
        health = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": []},
            "srm": {"status": "Healthy", "p_value": 0.9}
        }
        primary = {"is_significant": False, "p_value": 0.3, "absolute_lift": 0.001}
        guardrails = []
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "비유의" in result["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
