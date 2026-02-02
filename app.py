"""
ExperimentOS — A/B 테스트 실험 운영·검증·의사결정 자동화 도구

Streamlit 기반 Decision Layer MVP
"""

import streamlit as st
from src.experimentos.state import initialize_state
from src.experimentos.logger import setup_logger

# 페이지 설정
st.set_page_config(
    page_title="ExperimentOS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로거 설정
logger = setup_logger()

# Session state 초기화
initialize_state()

# 메인 페이지
st.title("🧪 ExperimentOS")
st.markdown("""
### A/B 테스트 실험 Decision Layer

실험 결과 데이터를 넣으면 **SRM·효과크기(신뢰구간)·가드레일**을 표준으로 자동 검증하고,  
**Launch/Hold/Rollback 결정 메모(1pager)**를 생성합니다.

---

#### 사용 방법

1. **📂 New Experiment**: CSV 파일 업로드 및 Health Check
2. **📊 Results**: Primary 분석 및 Guardrail 비교 결과 확인
3. **📝 Decision Memo**: 1pager Decision Memo 생성 및 다운로드

---

#### 시작하기

왼쪽 사이드바에서 **New Experiment** 페이지로 이동하여 CSV 파일을 업로드하세요.
""")

# 상태 표시 (디버깅용, 나중에 제거 가능)
if st.checkbox("Show session state (debug)"):
    st.write("Current session state:", st.session_state)
