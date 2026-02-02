# ExperimentOS — 실험 운영·검증·의사결정 자동화 (Streamlit MVP)

실험(A/B) 데이터를 넣으면 **SRM/효과(신뢰구간)/가드레일**을 자동 검증하고,  
**Launch/Hold/Rollback 결정 메모(1pager)**를 생성해 실험 의사결정 속도와 일관성을 높이는 Streamlit MVP입니다.

> 이 프로젝트는 Hackle/Statsig/GrowthBook 같은 **실험 실행 플랫폼(Feature Flag/SDK/트래킹)**을 대체하지 않습니다.  
> 어떤 실험 도구에서든 뽑을 수 있는 “결과 데이터”를 입력으로 받아, **검증 표준화 + 결정 메모 자동화**를 제공하는 **Decision Layer**입니다.

📖 **[Architecture Documentation](./ARCHITECTURE.md)** — Tech stack, folder structure, coding conventions, and how to extend the system.

---

## Why (Problem)
실험 결과 공유 방식이 매번 달라서,
- SRM(표본 불균형)이나 가드레일 악화를 놓치고 “좋아 보이는 숫자”로 잘못 롤아웃할 수 있고
- 리뷰/검토가 반복되며 의사결정이 느려지는 문제가 생깁니다.

ExperimentOS는 **실험 운영의 표준(Health Check → Result → Decision Memo)**을 자동화해  
스쿼드가 빠르게 같은 결론에 도달하도록 돕습니다.

---

## Target Users
- **데이터 분석가(Primary)**: 실험 검증/리포트/결정 메모를 표준화해 리드타임을 줄이고 싶다.
- **PM/PO(Decision Maker)**: 통계 설명보다 “결론 + 근거 + 리스크 + 다음 액션”이 한 장으로 필요하다.
- **엔지니어/실험 운영 담당(Secondary)**: 롤아웃/롤백 판단 기준이 명확한 메모를 받아 실행하고 싶다.

---

## MVP Features
1) **CSV 업로드 + 스키마 검증**
- 필수: `variant(control/treatment)`, `users`, `conversions`
- 논리: `conversions <= users`, 음수 금지 등

2) **Health Check 자동화**
- SRM(chi-square) 자동 탐지 (기대 split 기본 50/50, 설정 가능)
- 결측/중복/라벨/타입 오류 체크
- 상태 배지: **Healthy / Warning / Blocked**

3) **Primary 결과 분석 (전환율)**
- conversion_rate 기반 `lift(절대/상대)`, `95% CI`, `p-value`
- 기본 검정: two-proportion z-test (양측)  
  *(작은 표본/극단 비율은 Fisher exact로 대체하는 옵션 권장)*

4) **Guardrail 비교**
- 선택한 guardrail 컬럼(control vs treatment) 비교
- 악화(worsened) 배지 표시 (임계치/유의성 규칙 기반)

5) **Decision Memo 1pager 자동 생성 + Export**
- 결론: Launch/Hold/Rollback (룰 기반)
- 근거/리스크/Next Actions 포함
- Markdown/HTML 다운로드

---

## Screens
- `docs/demo.gif` (추가 예정)

---

## Quickstart

### 1. 설치

```bash
# Clone repository
git clone <repository_url>
cd <project_directory>

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. 실행

```bash
streamlit run app.py
```

앱이 `http://localhost:8501`에서 실행됩니다.

### 3. 사용 방법

#### Step 1: New Experiment 페이지
1. 실험명 입력 (예: "홈화면 배너 A/B 테스트")
2. 기대 트래픽 분배 입력 (기본: 50:50)
3. CSV 파일 업로드
4. Health Check 자동 실행 및 결과 확인

#### Step 2: Results 페이지
1. Health Check 상태 확인
2. Primary Result (전환율 분석) 확인
3. Guardrail 테이블 확인
4. Decision 배지 확인 (🚀Launch / ⏸️Hold / 🔙Rollback)

#### Step 3: Decision Memo 페이지
1. 1pager Decision Memo 프리뷰
2. Markdown 또는 HTML 다운로드

### 4. 샘플 CSV 파일

프로젝트에 3개 샘플 CSV가 포함되어 있습니다 (`.tmp/` 디렉토리):

1. **sample_launch.csv**: 정상 실험 → Launch
2. **sample_srm_warning.csv**: SRM 경고 → Hold
3. **sample_guardrail_worsened.csv**: Guardrail 악화 → Hold/Rollback

---

## Input Data Format (CSV)

### 필수 컬럼
- **variant**: `control` 또는 `treatment` (2개 variant만 지원, MVP)
- **users**: 각 variant 유저 수 (int, > 0)
- **conversions**: 전환 수 (int, 0 이상, users 이하)

### 옵션 컬럼 (Guardrails)
- 예: `guardrail_cancel`, `guardrail_refund`, `guardrail_error`, `revenue` 등
- MVP에서는 기본적으로 **카운트형 guardrail (율 = count/users)** 을 가정합니다.

### 예시 (sample.csv)
```csv
variant,users,conversions,guardrail_cancel,guardrail_error
control,10000,1200,120,35
treatment,10050,1320,118,33
```

---

## Decision Rules (MVP)

기본 룰 (요약):

1. **Blocked** (스키마/논리 오류) → **Hold**
2. **SRM 경고** (p < 0.001 또는 p < 0.00001) → **Hold**
3. **Primary 유의** (p < 0.05) + **Severe Guardrail 악화** → **Rollback**
4. **Primary 유의** + **일반 Guardrail 악화** → **Hold**
5. **Primary 유의** + **Guardrail 정상** → **Launch**
6. **Primary 비유의** (p >= 0.05) → **Hold**

### Guardrail 악화 기준
- **Worsened**: Δ > 0.1%p (0.001)
- **Severe**: Δ > 0.3%p (0.003)

---

## Pages (Streamlit)

1. **Home**: 현재 세션 상태 요약 / 빠른 시작 가이드
2. **New Experiment**: CSV 업로드 / 메타 입력 / Health Check 자동 실행
3. **Results**: Health Check + Primary + Guardrail 결과 + Decision
4. **Decision Memo**: 1pager 미리보기 + MD/HTML export

---

## Tech Stack

- **Frontend/UI**: Streamlit (멀티페이지)
- **Backend/Analysis**: Python (pandas, numpy, scipy, statsmodels)
- **Storage (MVP)**: Streamlit session_state
- **Export**: Markdown, HTML

---

## Project Structure

```
.
├── app.py                      # 메인 엔트리 포인트
├── pages/
│   ├── 1_Home.py              # Home 페이지
│   ├── 2_New_Experiment.py    # CSV 업로드 & Health Check
│   ├── 3_Results.py           # 분석 결과 & Decision
│   └── 4_Decision_Memo.py     # Memo 생성 & Export
├── src/experimentos/
│   ├── __init__.py
│   ├── state.py               # Session state 관리
│   ├── logger.py              # 로깅 설정
│   ├── healthcheck.py         # 스키마 검증 & SRM 탐지
│   ├── analysis.py            # Primary & Guardrail 분석
│   └── memo.py                # Decision 룰 엔진 & Memo 생성
├── tests/
│   ├── test_healthcheck.py
│   ├── test_analysis.py
│   └── test_decision.py
├── .tmp/                      # 샘플 CSV 파일
└── requirements.txt
```

---

## Quality / Tests

### 단위 테스트 (pytest)
```bash
python -m pytest tests/ -v
```

**테스트 커버리지**:
- SRM 탐지 케이스 (정상/경고/Blocked)
- `conversions > users` 차단
- Primary 계산 (Lift, CI, p-value)
- Decision 룰 분기 (Launch/Hold/Rollback)

### 실행 전 수동 체크
- [ ] 업로드 없이 Results/Decision Memo 진입 시 친절한 안내가 뜨는가?
- [ ] SRM 실패 데이터에서 Warning/Hold가 나오는가?
- [ ] Guardrail 악화 데이터에서 Hold/Rollback으로 가는가?
- [ ] MD/HTML 다운로드가 정상 동작하는가?

---

## Limitations

- MVP는 **집계형 입력** 기반 (이벤트 레벨/코호트 분석은 확장 범위)
- 고급 기법 (CUPED/층화/순차검정 등)은 기본 포함하지 않음
- 실제 Feature flag/배포/롤아웃 시스템과 직접 연동하지 않음

---

## Roadmap (Next)

- **(V1)** 실험 히스토리 DB 저장 (SQLite/DuckDB)
- **(V1)** Segment breakdown (신규/복귀/헤비) 탭
- **(V1)** CUPED 또는 층화 1개만 선택 적용
- **(V2)** Notion/Confluence export 템플릿 최적화
- **(V2)** 이벤트 레벨 분석 지원

---

## Data / Ethics

- 개인정보/회사 기밀 데이터 사용 금지
- 공개 데이터 또는 합성 데이터만 사용
- 가정/제약은 README 및 Decision Memo에 명시

---

## License

MIT

---

## Contributors

ExperimentOS MVP Project Team
