"""
Results 페이지

Health Check, Primary 분석, Guardrail 비교, Continuous, Bayesian 결과
"""

import streamlit as st
import pandas as pd
from src.experimentos.state import initialize_state, has_data, has_health_check
from src.experimentos.analysis import (
    calculate_primary, 
    calculate_guardrails,
    calculate_continuous_metrics,
    calculate_bayesian_insights
)
from src.experimentos.memo import make_decision

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

# 1. Health Check & Decision Summary
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1️⃣ Health Check")
    if has_health_check():
        health_result = st.session_state.health_result
        overall_status = health_result["overall_status"]
        if overall_status == "Healthy":
            st.success("✅ **Healthy**")
        elif overall_status == "Warning":
            st.warning("⚠️ **Warning**")
        else:
            st.error("🚫 **Blocked**")
    else:
        st.info("Health Check 결과 없음")

with col2:
    st.subheader("4️⃣ Decision Prediction")
    # This will be fully calculated in memo, but we show a preview here if possible
    # We need primary result first
    pass


st.markdown("---")

# Analysis Execution
try:
    # Primary
    primary_result = calculate_primary(df)
    st.session_state.primary_result = primary_result
    
    # Guardrails
    guardrails = calculate_guardrails(df)
    st.session_state.guardrails = guardrails
    
    # Continuous
    continuous_results = calculate_continuous_metrics(df)
    st.session_state.continuous_results = continuous_results
    
    # Bayesian (Informational)
    bayesian_insights = calculate_bayesian_insights(df, continuous_results)
    st.session_state.bayesian_insights = bayesian_insights
    
    # Decision (Real-time update)
    if has_health_check():
        decision_result = make_decision(
            health=st.session_state.health_result,
            primary=st.session_state.primary_result,
            guardrails=st.session_state.get("guardrails", [])
        )
        st.session_state.decision = decision_result
        
        # Update Decision Preview in col2
        with col2:
            d = decision_result["decision"]
            if d == "Launch":
                st.success(f"🚀 **{d}**")
            elif d == "Rollback":
                st.error(f"🔙 **{d}**")
            else:
                st.warning(f"⏸️ **{d}**")

except Exception as e:
    st.error(f"분석 중 치명적 오류 발생: {e}")
    st.stop()


# 2. Tabs View
tabs_list = ["Primary"]
if continuous_results:
    tabs_list.append("Continuous")
tabs_list.append("Guardrails")
tabs_list.append("Bayesian View")

tabs = st.tabs(tabs_list)

# --- Tab: Primary ---
with tabs[0]:
    st.caption("Primary Metric (Conversion Rate) Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Control Rate", f"{primary_result['control']['rate']:.2%}")
    with col2:
        st.metric("Treatment Rate", f"{primary_result['treatment']['rate']:.2%}", 
                  delta=f"{primary_result['absolute_lift']:.2%}p")
    with col3:
        st.metric("Relative Lift", f"{primary_result['relative_lift']:+.1%}")
    with col4:
        is_sig = primary_result['is_significant']
        st.metric("Significance", "✅ 유의함" if is_sig else "❌ 유의하지 않음", 
                  help=f"p={primary_result['p_value']:.4f}")
        
    with st.expander("📈 상세 통계 정보 (Confidence Interval)"):
        ci = primary_result['ci_95']
        st.code(f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}] ({ci[0]*100:.2f}%p ~ {ci[1]*100:.2f}%p)")
        st.code(f"P-value: {primary_result['p_value']:.6f}")


# --- Tab: Continuous (Conditional) ---
if continuous_results:
    tab_idx = tabs_list.index("Continuous")
    with tabs[tab_idx]:
        st.caption("Continuous Metrics Analysis (Welch's t-test)")
        
        for res in continuous_results:
            st.markdown(f"#### 📊 {res['metric_name']}")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(f"Control Mean", f"{res['control_mean']:.2f}")
            with c2:
                st.metric(f"Treatment Mean", f"{res['treatment_mean']:.2f}", 
                          delta=f"{res['absolute_lift']:.2f}")
            with c3:
                st.metric("Relative Lift", f"{res['relative_lift']:+.1%}")
            with c4:
                sig_icon = "✅" if res['is_significant'] else "❌"
                st.metric("Significance", f"{sig_icon} (p={res['p_value']:.3f})")
            
            st.divider()


# --- Tab: Guardrails ---
tab_idx = tabs_list.index("Guardrails")
with tabs[tab_idx]:
    st.caption("Guardrail Metrics Analysis")
    if guardrails:
        # Guardrail Table
        g_df = pd.DataFrame([
            {
                "Metric": g["name"],
                "Control": f"{g['control_rate']:.2%} ({g['control_count']:,})",
                "Treatment": f"{g['treatment_rate']:.2%} ({g['treatment_count']:,})",
                "Δ": f"{g['delta']:+.2%}p",
                "Status": "🚫 Severe" if g["severe"] else ("⚠️ Worsened" if g["worsened"] else "✅ OK")
            }
            for g in guardrails
        ])
        st.dataframe(g_df, use_container_width=True, hide_index=True)
    else:
        st.info("Guardrail 지표가 없습니다 (자동 탐지됨).")


# --- Tab: Bayesian View ---
tab_idx = tabs_list.index("Bayesian View")
with tabs[tab_idx]:
    st.info("ℹ️ **참고용 (Informational Only)**: 베이지안 분석 결과는 의사결정 규칙(Launch/Hold/Rollback)에 영향을 주지 않습니다.")
    
    # 1. Conversion
    b_conv = bayesian_insights.get("conversion")
    if b_conv:
        prob = b_conv["prob_treatment_beats_control"]
        loss = b_conv["expected_loss"]
        
        st.markdown("### Primary Metric (Conversion)")
        st.progress(prob, text=f"Probability Treatment > Control: **{prob:.1%}**")
        st.caption(f"Expected Loss (Risk): {loss:.6f}")
        
    # 2. Continuous
    b_cont = bayesian_insights.get("continuous")
    if b_cont:
        st.markdown("### Continuous Metrics")
        for metric, res in b_cont.items():
            prob = res["prob_treatment_beats_control"]
            st.progress(prob, text=f"**{metric}**: Probability Treatment > Control: **{prob:.1%}**")

st.markdown("""
---
### 다음 단계
Decision Memo 페이지에서 최종 리포트를 확인하세요.
""")
