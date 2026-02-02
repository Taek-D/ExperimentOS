"""
Navigation Guards 단위 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import streamlit as st
from unittest.mock import MagicMock
from src.experimentos.state import get_health_status_banner


class TestGetHealthStatusBanner:
    """get_health_status_banner() 함수 테스트"""
    
    def setup_method(self):
        """각 테스트 전 session state 초기화"""
        # Streamlit session state mock
        st.session_state.clear()
    
    def test_no_health_check_returns_none(self):
        """Health Check 결과가 없으면 None 반환"""
        severity, messages = get_health_status_banner()
        
        assert severity is None
        assert messages == []
    
    def test_healthy_status_returns_none(self):
        """Healthy 상태는 None 반환"""
        st.session_state.health_result = {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.5}
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity is None
        assert messages == []
    
    def test_blocked_with_schema_issues(self):
        """Blocked 상태 - 스키마 이슈"""
        st.session_state.health_result = {
            "overall_status": "Blocked",
            "schema": {
                "status": "Blocked",
                "issues": [
                    "필수 컬럼 누락: conversions",
                    "users에 음수 값이 있습니다"
                ]
            },
            "srm": None
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Blocked"
        assert len(messages) == 2
        assert "필수 컬럼 누락" in messages[0]
        assert "음수" in messages[1]
    
    def test_warning_with_srm_issue(self):
        """Warning 상태 - SRM 이슈"""
        st.session_state.health_result = {
            "overall_status": "Warning",
            "schema": {
                "status": "Warning",
                "issues": ["⚠️ Warning: users가 100 미만인 행이 있습니다."]
            },
            "srm": {
                "status": "Warning",
                "p_value": 0.0005,
                "message": "SRM 경고 (p=0.0005). 트래픽 분배를 확인하세요."
            }
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Warning"
        assert len(messages) == 2
        assert "100 미만" in messages[0]
        assert "SRM 경고" in messages[1]
    
    def test_blocked_with_severe_srm(self):
        """Blocked 상태 - Severe SRM"""
        st.session_state.health_result = {
            "overall_status": "Blocked",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {
                "status": "Blocked",
                "p_value": 0.000001,
                "message": "심각한 SRM 탐지 (p=1.00e-06). 실험 데이터를 검토하세요."
            }
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Blocked"
        assert len(messages) == 1
        assert "심각한 SRM" in messages[0]
    
    def test_filters_out_healthy_issues(self):
        """검증 통과 메시지는 필터링"""
        st.session_state.health_result = {
            "overall_status": "Warning",
            "schema": {
                "status": "Warning",
                "issues": [
                    "검증 통과",  # Should be filtered
                    "⚠️ Warning: users가 100 미만인 행이 있습니다."
                ]
            },
            "srm": None
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Warning"
        assert len(messages) == 1
        assert "100 미만" in messages[0]
    
    def test_empty_issues_list(self):
        """이슈 리스트가 비어있는 경우"""
        st.session_state.health_result = {
            "overall_status": "Warning",
            "schema": {"status": "Warning", "issues": []},
            "srm": None
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Warning"
        assert messages == []
    
    def test_srm_healthy_not_included(self):
        """SRM Healthy는 메시지에 포함되지 않음"""
        st.session_state.health_result = {
            "overall_status": "Warning",
            "schema": {
                "status": "Warning",
                "issues": ["작은 표본"]
            },
            "srm": {
                "status": "Healthy",
                "p_value": 0.8,
                "message": "SRM 정상"
            }
        }
        
        severity, messages = get_health_status_banner()
        
        assert severity == "Warning"
        assert len(messages) == 1
        assert "작은 표본" in messages[0]
        assert "SRM" not in messages[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
