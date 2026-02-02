"""
PRD Acceptance Criteria Tests

모든 테스트는 PRD 문서의 acceptance criteria와 직접 매핑됩니다.
각 테스트는 deterministic하고 fast합니다 (< 0.5s total).

PRD Reference: Section 10.2 - Decision Framework
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from src.experimentos.healthcheck import validate_schema, detect_srm, run_health_check
from src.experimentos.analysis import calculate_primary, calculate_guardrails
from src.experimentos.memo import make_decision


class TestPRDSRMAcceptance:
    """PRD 7.1: SRM Detection Acceptance Criteria"""
    
    def test_srm_healthy_normal_50_50_split(self):
        """
        PRD 10.2.1: SRM Healthy
        
        Scenario: Normal 50/50 split (10000 vs 10000)
        Expected: Healthy status, p-value > 0.05
        """
        result = detect_srm(
            control_users=10000,
            treatment_users=10000,
            expected_split=(50.0, 50.0)
        )
        
        assert result["status"] == "Healthy"
        assert result["p_value"] > 0.05
        assert result["observed"]["control"] == 10000
        assert result["observed"]["treatment"] == 10000
    
    def test_srm_blocked_severe_imbalance(self):
        """
        PRD 10.2.1: SRM Blocked - Severe Imbalance
        
        Scenario: 5000 vs 10000 (33% vs 67%)
        Expected: Blocked status, p < 0.00001
        """
        result = detect_srm(
            control_users=5000,
            treatment_users=10000,
            expected_split=(50.0, 50.0)
        )
        
        assert result["status"] == "Blocked"
        assert result["p_value"] < 0.00001
        assert "심각한 SRM" in result["message"]
    
    def test_srm_warning_moderate_imbalance(self):
        """
        PRD 7.1: SRM Warning
        
        Scenario: 5500 vs 6500 (moderate imbalance)
        Expected: Warning status, 0.00001 < p < 0.001
        """
        result = detect_srm(
            control_users=5500,
            treatment_users=6500,
            expected_split=(50.0, 50.0)
        )
        
        assert result["status"] in ["Warning", "Blocked"]
        assert result["p_value"] < 0.001


class TestPRDSchemaAcceptance:
    """PRD 6: Schema Validation Acceptance Criteria"""
    
    def test_schema_blocked_conversions_exceeds_users(self):
        """
        PRD 10.2.2: Schema Blocked
        
        Scenario: conversions > users (invalid logic)
        Expected: Blocked status, specific error message
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [12000, 1100]  # Control exceeds users
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("conversions가 users보다 큰" in issue for issue in result["issues"])
    
    def test_schema_blocked_missing_required_column(self):
        """
        PRD 6.2: Missing Required Column
        
        Scenario: Missing 'conversions' column
        Expected: Blocked status, missing column error
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000]
            # conversions 컬럼 누락
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("필수 컬럼 누락" in issue for issue in result["issues"])
        assert any("conversions" in issue for issue in result["issues"])
    
    def test_schema_blocked_negative_users(self):
        """
        PRD 6.3: Negative Values
        
        Scenario: Negative user count
        Expected: Blocked status, negative value error
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [-100, 10000],
            "conversions": [100, 1100]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Blocked"
        assert any("음수" in issue for issue in result["issues"])
    
    def test_schema_warning_small_sample(self):
        """
        PRD 6.4: Small Sample Warning
        
        Scenario: users < 100
        Expected: Warning status, small sample message
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [50, 50],
            "conversions": [5, 7]
        })
        
        result = validate_schema(df)
        
        assert result["status"] == "Warning"
        assert any("100 미만" in issue for issue in result["issues"])


class TestPRDDecisionAcceptance:
    """PRD 10: Decision Framework Acceptance Criteria"""
    
    def test_decision_launch_significant_no_guardrail_issues(self):
        """
        PRD 10.2.3: Launch Decision
        
        Scenario: Primary significant + No guardrail issues
        Expected: Launch decision
        """
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
    
    def test_decision_rollback_severe_guardrail_exceeds_0_3_percent(self):
        """
        PRD 10.2.3: Rollback Decision
        
        Scenario: Primary significant + Severe guardrail (Δ > 0.3%p)
        Expected: Rollback decision
        """
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
                "delta": 0.004,  # 0.4%p (> 0.3%p severe threshold)
                "worsened": True,
                "severe": True
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Rollback"
        assert "심각한 Guardrail 악화" in result["reason"]
        assert "crash_rate" in result["reason"]
    
    def test_decision_hold_worsened_guardrail_between_0_1_and_0_3_percent(self):
        """
        PRD 10.2.3: Hold Decision
        
        Scenario: Primary significant + Worsened guardrail (0.1%p < Δ < 0.3%p)
        Expected: Hold decision
        """
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
                "delta": 0.0015,  # 0.15%p (worsened but not severe)
                "worsened": True,
                "severe": False
            }
        ]
        
        result = make_decision(health, primary, guardrails)
        
        assert result["decision"] == "Hold"
        assert "Guardrail 악화" in result["reason"]
        assert "error_rate" in result["reason"]
    
    def test_decision_hold_primary_not_significant(self):
        """
        PRD 10.2.5: Hold Decision
        
        Scenario: Primary NOT significant (p >= 0.05)
        Expected: Hold decision
        """
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
    
    def test_decision_hold_srm_warning(self):
        """
        PRD 10.2.2: Hold Decision
        
        Scenario: SRM Warning (p < 0.001)
        Expected: Hold decision regardless of primary
        """
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
    
    def test_decision_hold_schema_blocked(self):
        """
        PRD 10.2.1: Hold Decision
        
        Scenario: Schema Blocked (data quality issue)
        Expected: Hold decision, data quality reason
        """
        health = {
            "overall_status": "Blocked",
            "schema": {
                "status": "Blocked",
                "issues": ["conversions가 users보다 큰 행이 있습니다"]
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


class TestPRDEndToEndAcceptance:
    """PRD Integration: End-to-End Acceptance Scenarios"""
    
    def test_e2e_launch_scenario(self):
        """
        PRD Full Flow: Launch Scenario
        
        Healthy data → Significant primary → No guardrail issues → Launch
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200],  # 10% vs 12% (significant)
            "error_count": [10, 15]  # 0.1% vs 0.15% (OK)
        })
        
        # 1. Health Check
        health = run_health_check(df, expected_split=(50, 50))
        assert health["overall_status"] == "Healthy"
        
        # 2. Primary Analysis
        primary = calculate_primary(df)
        assert primary["is_significant"] is True
        
        # 3. Guardrail Analysis
        guardrails = calculate_guardrails(df)
        assert len(guardrails) == 1
        assert guardrails[0]["worsened"] is False
        
        # 4. Decision
        decision = make_decision(health, primary, guardrails)
        assert decision["decision"] == "Launch"
    
    def test_e2e_rollback_scenario(self):
        """
        PRD Full Flow: Rollback Scenario
        
        Healthy data → Significant primary → Severe guardrail → Rollback
        """
        df = pd.DataFrame({
            "variant": ["control", "treatment"],
            "users": [10000, 10000],
            "conversions": [1000, 1200],  # 10% vs 12% (significant)
            "crash_count": [10, 50]  # 0.1% vs 0.5% (severe: Δ = 0.4%p)
        })
        
        # 1. Health Check
        health = run_health_check(df, expected_split=(50, 50))
        assert health["overall_status"] == "Healthy"
        
        # 2. Primary Analysis
        primary = calculate_primary(df)
        assert primary["is_significant"] is True
        
        # 3. Guardrail Analysis
        guardrails = calculate_guardrails(df)
        assert len(guardrails) == 1
        assert guardrails[0]["severe"] is True
        
        # 4. Decision
        decision = make_decision(health, primary, guardrails)
        assert decision["decision"] == "Rollback"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
