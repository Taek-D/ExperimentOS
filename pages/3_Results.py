"""
Results 페이지

Health Check, Primary 분석, Guardrail 비교 결과
"""

import streamlit as st
from src.experimentos.state import initialize_state, has_data, has_health_check
from src.experimentos.analysis import calculate_primary

# State 초기화
initialize_state()

st.title("📊 Results")

# 데이터 확인
if not has_data():
    st.warning("⚠️ 데이터가 없습니다. New Experiment 페이지에서 CSV 파일을 업로드하세요.")
    if st.button("📂 New Experiment로 이동"):
        st.info("사이드바에서 'New Experiment'를 클릭하세요.")
    st.stop()

# 데이터 로드
df = st.session_state.data

st.markdown("""
### 분석 결과

---
""")

# Status Banner (Blocked/Warning)
from src.experimentos.state import get_health_status_banner

severity, messages = get_health_status_banner()

if severity == "Blocked":
    st.error("🚫 **데이터 품질 문제 (Blocked)**")
    st.markdown("**발견된 이슈:**")
    for msg in messages:
        st.write(f"- {msg}")
    st.info("위의 이슈를 수정한 후 다시 업로드하세요.")
    st.markdown("---")
elif severity == "Warning":
    st.warning("⚠️ **경고 (Warning)**")
    st.markdown("**발견된 이슈:**")
    for msg in messages:
        st.write(f"- {msg}")
    st.info("경고가 있지만 분석은 가능합니다. 주의하여 해석하세요.")
    st.markdown("---")

# 1. Health Check 결과 표시
st.subheader("1️⃣ Health Check")

if has_health_check():
    health_result = st.session_state.health_result
    overall_status = health_result["overall_status"]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if overall_status == "Healthy":
            st.success("✅ **Healthy**")
        elif overall_status == "Warning":
            st.warning("⚠️ **Warning**")
        else:
            st.error("🚫 **Blocked**")
    
    with col2:
        # SRM 결과 요약
        if health_result["srm"]:
            srm = health_result["srm"]
            st.write(f"- SRM Status: **{srm['status']}** (p={srm['p_value']:.4f})")
        
        # 스키마 이슈 요약
        issues = health_result["schema"]["issues"]
        if issues and "검증 통과" not in issues:
            st.write(f"- Issues: {len(issues)}건 발견")
else:
    st.info("Health Check 결과가 없습니다. New Experiment 페이지에서 검증을 실행하세요.")


st.markdown("---")

# 2. Primary Result (전환율)
st.subheader("2️⃣ Primary Result (Conversion Rate)")

# Primary 분석 실행
try:
    primary_result = calculate_primary(df)
    st.session_state.primary_result = primary_result
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Control Rate",
            value=f"{primary_result['control']['rate']:.2%}",
            help=f"{primary_result['control']['conversions']:,} / {primary_result['control']['users']:,}"
        )
        
    with col2:
        st.metric(
            label="Treatment Rate",
            value=f"{primary_result['treatment']['rate']:.2%}",
            delta=f"{primary_result['absolute_lift']:.2%}p",
            help=f"{primary_result['treatment']['conversions']:,} / {primary_result['treatment']['users']:,}"
        )
        
    with col3:
        st.metric(
            label="Relative Lift",
            value=f"{primary_result['relative_lift']:+.1%}",
            delta_color="normal"
        )
        
    with col4:
        is_sig = primary_result['is_significant']
        sig_text = "✅ 유의함" if is_sig else "❌ 유의하지 않음"
        st.metric(
            label="Statistical Significance",
            value=sig_text,
            help=f"p-value: {primary_result['p_value']:.4f}"
        )
    
    # 상세 통계
    with st.expander("📈 상세 통계 정보"):
        st.write("**95% 신뢰구간 (Absolute Lift):**")
        ci = primary_result['ci_95']
        st.code(f"[{ci[0]:.4f}, {ci[1]:.4f}] ({ci[0]*100:.2f}%p ~ {ci[1]*100:.2f}%p)")
        
        st.write("**P-value:**")
        st.code(f"{primary_result['p_value']:.6f}")
        
        if is_sig:
            st.success(f"p-value ({primary_result['p_value']:.4f}) < 0.05 이므로, 두 그룹 간의 차이는 통계적으로 유의합니다.")
        else:
            st.info(f"p-value ({primary_result['p_value']:.4f}) >= 0.05 이므로, 두 그룹 간의 차이는 우연일 가능성이 있습니다.")

except Exception as e:
    st.error(f"Primary 분석 중 오류 발생: {e}")


st.markdown("---")

# 3. Guardrail 비교
st.subheader("3️⃣ Guardrails")

try:
    from src.experimentos.analysis import calculate_guardrails
    from src.experimentos.memo import make_decision
    
    guardrails = calculate_guardrails(df)
    st.session_state.guardrails = guardrails
    
    if guardrails:
        # Guardrail 테이블
        import pandas as pd
        
        guardrail_table = pd.DataFrame([
            {
                "Metric": g["name"],
                "Control": f"{g['control_rate']:.2%} ({g['control_count']:,})",
                "Treatment": f"{g['treatment_rate']:.2%} ({g['treatment_count']:,})",
                "Δ": f"{g['delta']:+.2%}p",
                "Status": "🚫 Severe" if g["severe"] else ("⚠️ Worsened" if g["worsened"] else "✅ OK")
            }
            for g in guardrails
        ])
        
        st.dataframe(guardrail_table, width="stretch", hide_index=True)
        
        # 악화된 Guardrail 요약
        worsened = [g for g in guardrails if g["worsened"]]
        if worsened:
            st.warning(f"⚠️ {len(worsened)}개 Guardrail 악화 감지")
    else:
        st.info("Guardrail 지표가 없습니다.")

except Exception as e:
    st.error(f"Guardrail 분석 중 오류 발생: {e}")


st.markdown("---")

# 4. Decision
st.subheader("4️⃣ Decision")

try:
    if has_health_check() and st.session_state.get("primary_result"):
        decision_result = make_decision(
            health=st.session_state.health_result,
            primary=st.session_state.primary_result,
            guardrails=st.session_state.get("guardrails", [])
        )
        
        st.session_state.decision = decision_result
        
        decision = decision_result["decision"]
        
        # Decision 배지
        if decision == "Launch":
            st.success(f"🚀 **{decision}**")
        elif decision == "Rollback":
            st.error(f"🔙 **{decision}**")
        else:
            st.warning(f"⏸️ **{decision}**")
        
        st.write(f"**근거**: {decision_result['reason']}")
        
        # 상세 근거
        with st.expander("📋 상세 근거"):
            for detail in decision_result["details"]:
                st.write(f"- {detail}")
    
    else:
        st.info("Health Check 및 Primary 분석 결과가 필요합니다.")

except Exception as e:
    st.error(f"Decision 생성 중 오류 발생: {e}")


st.markdown("""
---

### 다음 단계

Decision Memo 페이지에서 1pager를 다운로드하세요.
""")

