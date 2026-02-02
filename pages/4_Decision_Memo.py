"""
Decision Memo 페이지

1pager Decision Memo 생성 및 다운로드
"""

import streamlit as st
from src.experimentos.state import initialize_state, has_data, has_health_check
from src.experimentos.memo import generate_memo, export_html

# State 초기화
initialize_state()

st.title("📝 Decision Memo")

# Consolidated Navigation Guard
missing_prerequisites = []

if not has_data():
    missing_prerequisites.append("❌ 데이터 업로드")
else:
    missing_prerequisites.append("✅ 데이터 업로드")

if not has_health_check():
    missing_prerequisites.append("❌ Health Check")
else:
    missing_prerequisites.append("✅ Health Check")

if not st.session_state.get("primary_result"):
    missing_prerequisites.append("❌ Primary 분석")
else:
    missing_prerequisites.append("✅ Primary 분석")

if not st.session_state.get("decision"):
    missing_prerequisites.append("❌ Decision 생성")
else:
    missing_prerequisites.append("✅ Decision 생성")

# 필수 prerequisites 체크
all_complete = (
    has_data() and
    has_health_check() and
    st.session_state.get("primary_result") and
    st.session_state.get("decision")
)

if not all_complete:
    st.warning("⚠️ **Decision Memo 생성 조건이 충족되지 않았습니다.**")
    
    st.markdown("**Prerequisites:**")
    for prereq in missing_prerequisites:
        st.write(f"  - {prereq}")
    
    st.info("👉 모든 단계를 완료하려면 **New Experiment** → **Results** 순서로 진행하세요.")
    
    if st.button("📂 New Experiment로 이동"):
        st.info("사이드바에서 'New Experiment'를 클릭하세요.")
    
    st.stop()

st.markdown("""
### Decision Memo (1pager)

실험 결과를 요약한 의사결정 메모입니다.

---
""")

# Memo 생성
try:
    experiment_name = st.session_state.get("experiment_name", "실험명 없음")
    
    memo_markdown = generate_memo(
        experiment_name=experiment_name,
        decision=st.session_state.decision,
        health=st.session_state.health_result,
        primary=st.session_state.primary_result,
        guardrails=st.session_state.get("guardrails", [])
    )
    
    # Memo 저장
    st.session_state.memo_markdown = memo_markdown
    
    # 프리뷰
    st.subheader("📄 Memo Preview")
    st.markdown(memo_markdown)
    
    st.markdown("---")
    
    # Download 버튼
    st.subheader("💾 Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Download as Markdown",
            data=memo_markdown,
            file_name=f"decision_memo_{experiment_name.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        # HTML Export
        html_content = export_html(memo_markdown)
        
        st.download_button(
            label="📥 Download as HTML",
            data=html_content,
            file_name=f"decision_memo_{experiment_name.replace(' ', '_')}.html",
            mime="text/html",
            use_container_width=True
        )

except Exception as e:
    st.error(f"Memo 생성 중 오류 발생: {e}")
    import traceback
    st.code(traceback.format_exc())
