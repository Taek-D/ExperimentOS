"""
New Experiment 페이지

CSV 업로드 및 Health Check
"""

import streamlit as st
import pandas as pd
from datetime import date
from src.experimentos.state import initialize_state, reset_state
from src.experimentos.healthcheck import run_health_check

# State 초기화
initialize_state()

st.title("📂 New Experiment")

# 새 실험 시작 버튼
if st.button("🔄 새 실험 시작 (상태 초기화)"):
    reset_state()
    st.success("✅ 상태가 초기화되었습니다.")
    st.rerun()

st.markdown("""
### CSV 파일 업로드

실험 결과 데이터를 업로드하세요.

**필수 컬럼**:
- `variant`: "control" 또는 "treatment"
- `users`: 유저 수 (정수)
- `conversions`: 전환 수 (정수, `conversions <= users`)

**옵션 컬럼** (Guardrails):
- `guardrail_error`, `guardrail_cancel` 등 (정수)

---
""")

# 실험 메타데이터 입력
st.subheader("1️⃣ 실험 정보")

col1, col2 = st.columns(2)
with col1:
    experiment_name = st.text_input(
        "실험명",
        value=st.session_state.get("experiment_name", ""),
        placeholder="예: 홈화면 배너 A/B 테스트"
    )
    st.session_state.experiment_name = experiment_name

with col2:
    expected_split_input = st.text_input(
        "기대 트래픽 분배 (control:treatment)",
        value="50:50",
        help="예: 50:50 (기본값) 또는 60:40"
    )

# expected_split 파싱
try:
    split_parts = expected_split_input.split(":")
    if len(split_parts) == 2:
        expected_split = (float(split_parts[0]), float(split_parts[1]))
    else:
        expected_split = (50.0, 50.0)
        st.warning("⚠️ 잘못된 형식. 기본값 50:50을 사용합니다.")
except:
    expected_split = (50.0, 50.0)
    st.warning("⚠️ 잘못된 형식. 기본값 50:50을 사용합니다.")

st.session_state.expected_split = expected_split

st.markdown("---")

# CSV 업로더
st.subheader("2️⃣ 데이터 업로드")

uploaded_file = st.file_uploader(
    "CSV 파일 선택",
    type=["csv"],
    help="실험 결과가 집계된 CSV 파일을 업로드하세요."
)

if uploaded_file is not None:
    try:
        # CSV 읽기
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ 파일이 업로드되었습니다: {uploaded_file.name}")
        
        # 데이터 미리보기
        with st.expander("📄 데이터 미리보기"):
            st.dataframe(df, width="stretch")
        
        # Session state에 저장
        st.session_state.data = df
        
        st.markdown("---")
        
        # Health Check 실행
        st.subheader("3️⃣ Health Check")
        
        with st.spinner("🔍 데이터 검증 중..."):
            health_result = run_health_check(df, expected_split=expected_split)
        
        # 결과 저장
        st.session_state.health_result = health_result
        
        # 전체 상태 배지
        overall_status = health_result["overall_status"]
        
        if overall_status == "Healthy":
            st.success("✅ Health Check: **Healthy**")
        elif overall_status == "Warning":
            st.warning("⚠️ Health Check: **Warning**")
        else:
            st.error("🚫 Health Check: **Blocked**")
        
        # 스키마 검증 결과
        st.markdown("#### 📋 스키마 검증")
        schema_result = health_result["schema"]
        
        if schema_result["status"] == "Healthy":
            st.success(f"✅ {schema_result['status']}")
        elif schema_result["status"] == "Warning":
            st.warning(f"⚠️ {schema_result['status']}")
        else:
            st.error(f"🚫 {schema_result['status']}")
        
        if schema_result["issues"]:
            st.write("**이슈:**")
            for issue in schema_result["issues"]:
                if "Warning" in issue:
                    st.warning(f"  - {issue}")
                else:
                    st.write(f"  - {issue}")
        
        # SRM 결과 (스키마가 Blocked가 아닐 때만)
        if health_result["srm"]:
            st.markdown("#### 🔬 SRM (Sample Ratio Mismatch) 검증")
            srm_result = health_result["srm"]
            
            if srm_result["status"] == "Healthy":
                st.success(f"✅ {srm_result['message']}")
            elif srm_result["status"] == "Warning":
                st.warning(f"⚠️ {srm_result['message']}")
            else:
                st.error(f"🚫 {srm_result['message']}")
            
            # SRM 상세 정보
            with st.expander("📊 SRM 상세 정보"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**관측값 (Observed)**")
                    st.write(f"- Control: {srm_result['observed']['control']:,} ({srm_result['observed']['control_pct']:.1f}%)")
                    st.write(f"- Treatment: {srm_result['observed']['treatment']:,} ({srm_result['observed']['treatment_pct']:.1f}%)")
                
                with col2:
                    st.write("**기대값 (Expected)**")
                    st.write(f"- Control: {srm_result['expected']['control']:.0f} ({srm_result['expected']['control_pct']:.1f}%)")
                    st.write(f"- Treatment: {srm_result['expected']['treatment']:.0f} ({srm_result['expected']['treatment_pct']:.1f}%)")
                
                st.write(f"**통계:**")
                st.write(f"- Chi-square: {srm_result.get('chi2_stat', 'N/A'):.4f}")
                st.write(f"- p-value: {srm_result['p_value']:.6f}")
        
        st.markdown("---")
        
        # 다음 단계 안내
        if overall_status == "Blocked":
            st.error("🚫 **데이터 품질 문제로 인해 분석을 진행할 수 없습니다.**")
            st.info("위의 이슈를 수정한 후 다시 업로드하세요.")
        elif overall_status == "Warning":
            st.warning("⚠️ **경고가 있지만 분석은 가능합니다.**")
            st.info("👉 Results 페이지에서 분석 결과를 확인하세요.")
        else:
            st.success("✅ **데이터 품질이 정상입니다.**")
            st.info("👉 Results 페이지에서 분석 결과를 확인하세요.")
    
    except Exception as e:
        st.error(f"❌ 파일 처리 중 오류 발생: {str(e)}")
        st.session_state.data = None
        st.session_state.health_result = None

else:
    st.info("📂 CSV 파일을 업로드하세요.")
    
    # 샘플 CSV 다운로드 (나중에 추가 예정)
    st.markdown("""
    ---
    
    ### 📥 샘플 CSV
    
    샘플 CSV 파일은 PR#5에서 제공 예정입니다.
    
    **예시 형식:**
    ```csv
    variant,users,conversions,guardrail_error
    control,10000,1200,35
    treatment,10000,1320,33
    ```
    """)
