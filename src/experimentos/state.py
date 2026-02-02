"""
Session State 관리

Streamlit session_state를 초기화하고 관리하는 모듈
"""

import streamlit as st
from .config import DEFAULT_EXPECTED_SPLIT


def initialize_state():
    """
    Session state 초기화
    
    앱 시작 시 필요한 session state 키들을 기본값으로 설정합니다.
    """
    # 실험 메타데이터
    if "experiment_name" not in st.session_state:
        st.session_state.experiment_name = ""
    
    if "experiment_start_date" not in st.session_state:
        st.session_state.experiment_start_date = None
    
    if "experiment_end_date" not in st.session_state:
        st.session_state.experiment_end_date = None
    
    if "expected_split" not in st.session_state:
        st.session_state.expected_split = DEFAULT_EXPECTED_SPLIT
    
    # 업로드된 데이터
    if "data" not in st.session_state:
        st.session_state.data = None
    
    # Health Check 결과
    if "health_result" not in st.session_state:
        st.session_state.health_result = None
    
    # Primary 분석 결과
    if "primary_result" not in st.session_state:
        st.session_state.primary_result = None
    
    # Guardrail 분석 결과
    if "guardrails" not in st.session_state:
        st.session_state.guardrails = None
    
    # Decision 결과
    if "decision" not in st.session_state:
        st.session_state.decision = None
    
    # Decision Memo
    if "memo" not in st.session_state:
        st.session_state.memo = None


def reset_state():
    """
    모든 session state를 초기화
    
    새로운 실험을 시작할 때 사용합니다.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_state()


def has_data():
    """
    데이터가 업로드되었는지 확인
    
    Returns:
        bool: 데이터가 있으면 True, 없으면 False
    """
    return st.session_state.data is not None


def has_health_check():
    """
    Health Check가 완료되었는지 확인
    
    Returns:
        bool: Health Check 결과가 있으면 True, 없으면 False
    """
    return st.session_state.health_result is not None


def has_primary_result():
    """
    Primary 분석이 완료되었는지 확인
    
    Returns:
        bool: Primary 결과가 있으면 True, 없으면 False
    """
    return st.session_state.primary_result is not None


def get_health_status_banner():
    """
    Health Check 상태 배너 정보 추출
    
    Returns:
        tuple: (severity: str | None, messages: List[str])
            - severity: "Blocked" | "Warning" | None
            - messages: 이슈 메시지 리스트
    """
    if not has_health_check():
        return None, []
    
    health = st.session_state.health_result
    overall_status = health.get("overall_status")
    
    if overall_status not in ["Blocked", "Warning"]:
        return None, []
    
    messages = []
    
    # 스키마 이슈
    schema_issues = health.get("schema", {}).get("issues", [])
    for issue in schema_issues:
        if issue and "검증 통과" not in issue:
            messages.append(issue)
    
    # SRM 이슈
    if health.get("srm"):
        srm = health["srm"]
        if srm["status"] in ["Warning", "Blocked"]:
            messages.append(srm["message"])
    
    return overall_status, messages
