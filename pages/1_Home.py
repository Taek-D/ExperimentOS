"""
Home 페이지

실험 목록 및 최근 결과 요약 (MVP: 단순한 안내 화면)
"""

import streamlit as st

st.title("🏠 Home")

st.markdown("""
### 실험 목록

> MVP 버전에서는 Session 기반으로 작동합니다.  
> 실험 히스토리 저장 기능은 V1(NEXT)에서 추가됩니다.

---

### 현재 세션 상태

""")

# Session state 요약 표시
if st.session_state.get("data") is not None:
    st.success("✅ 데이터가 업로드되었습니다.")
    
    if st.session_state.get("health_result"):
        health_status = st.session_state.health_result.get("status", "Unknown")
        if health_status == "Healthy":
            st.success(f"✅ Health Check: {health_status}")
        elif health_status == "Warning":
            st.warning(f"⚠️ Health Check: {health_status}")
        else:
            st.error(f"🚫 Health Check: {health_status}")
    
    if st.session_state.get("primary_result"):
        st.info("📊 Primary 분석이 완료되었습니다.")
    
    if st.session_state.get("decision"):
        decision = st.session_state.decision.get("decision", "Unknown")
        st.info(f"📝 Decision: {decision}")
else:
    st.info("📂 New Experiment 페이지에서 CSV 파일을 업로드하세요.")

st.markdown("""
---

### 빠른 시작

1. **📂 New Experiment**: CSV 파일 업로드
2. **📊 Results**: 분석 결과 확인
3. **📝 Decision Memo**: 1pager 다운로드
""")
