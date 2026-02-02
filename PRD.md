# PRD.md — ExperimentOS (A/B 테스트 운영·검증·의사결정 자동화, Streamlit MVP)

## 0. 문서 정보
- 문서 버전: v0.2 (MVP)
- 제품명: ExperimentOS
- 범위: **집계(aggregated) A/B(2 variants)** 실험 결과를 입력받아  
  **Health Check(SRM/데이터 품질) → Primary 분석 → Guardrail 점검 → Decision Memo(1pager)**를 자동 생성
- 비목표(Non-goals): Feature flag/SDK/트래킹/할당/실시간 스트리밍 분석/PII 처리

---

## 1) 한 줄 정의 (One-liner)
실험 결과 데이터를 넣으면 **SRM·효과크기(신뢰구간)·가드레일**을 표준으로 자동 검증하고, **Launch/Hold/Rollback 결정 메모(1pager)**를 생성해 스쿼드 의사결정의 속도와 일관성을 높이는 Decision Layer 도구.

---

## 2) 문제 정의 (Problem)
현재 실험 결과 공유/검토 방식이 케이스마다 달라서:
- SRM(표본 비율 불균형)·가드레일 악화를 놓치고 “좋아 보이는 숫자”로 잘못 롤아웃할 수 있음
- 리뷰어가 매번 동일한 체크를 반복하면서 의사결정이 느려지고 기준이 흔들림

ExperimentOS는 실험 운영의 표준 플로우를 자동화한다:  
**Health Check → Result → Decision Memo(결론/근거/리스크/다음 액션)**

---

## 3) 타겟 사용자 (Personas)
### Persona A — 데이터 분석가 (Primary)
- 목표: 검증/리포트/결정 메모를 표준화해 리드타임 단축
- 페인: SRM/가드레일 누락, 포맷 통일 실패, 반복 검토 비용

### Persona B — PM/PO (Decision Maker)
- 목표: 통계 디테일보다 **결론 + 근거 + 리스크 + 다음 액션**을 한 장으로 파악
- 페인: 결과가 산발적이고 결론이 애매함

### Persona C — 엔지니어/실험 운영 (Secondary)
- 목표: 롤아웃/롤백 판단 근거와 조건(가드레일 모니터링)을 명확히 받음
- 페인: 기준 불명확으로 배포 판단 지연

---

## 4) MVP 목표 / 성공 지표
### 제품 목표
- “실험 결과 해석”을 표준화하여 **더 빨리, 더 안전하게** Launch/Hold/Rollback 결정을 내리게 한다.

### 성공 지표(예시)
- 리포트 생성 리드타임: 120분 → 20분 이하
- 리뷰 반복 횟수: 3회 → 1회 수준
- 실패 케이스 탐지 재현성: SRM/가드레일 악화 시 **경고 및 결론 보류가 일관되게 발생**

---

## 5) 범위 정의 (Scope)
### MVP In-scope
- **2 variants(A/B)** 집계 입력: control vs treatment
- Primary metric: 전환율(비율형, `conversions/users`)
- Guardrail: 기본은 **비율형(카운트/유저수)** 지표를 지원(예: error_count/users)  
  *(연속형(예: latency 평균)은 P1로 확장 가능)*
- 출력: 결과 테이블 + 상태 배지 + Decision Memo(마크다운/HTML)

### MVP Out-of-scope (Non-goals)
- 다변량/다군 실험(n>2 variants)
- CUPED/층화/순차검정(기본 미포함, P1+)
- 이벤트 레벨 분석(유저/이벤트 로그 기반)은 MVP 제외
- 배포/feature flag 시스템 연동

---

## 6) 입력 데이터 스키마 & 검증 규칙
### 6.1 입력 형식
- 파일: CSV (MVP), 옵션으로 Parquet/Paste SQL 결과(P1)
- 행: variant 단위 집계 (최소 2행: control, treatment)

### 6.2 필수 컬럼
- `variant`: `"control"` 또는 `"treatment"` (대소문자/공백 정규화)
- `users`: int, `users > 0`
- `conversions`: int, `0 <= conversions <= users`

### 6.3 Guardrail 컬럼(옵션)
- 기본 MVP: **카운트형 guardrail** (예: `guardrail_error`, `guardrail_cancel`)
  - 타입: int, `0 <= guardrail_x <= users` 권장(“유저당 1회” 가정인 경우)
  - 이벤트 카운트(유저당 다회 가능)라면 Memo에 “해석 주의”로 표기 (MVP에서는 Warning 처리 가능)

### 6.4 데이터 품질/논리 검증 (Health Check 입력단)
- 필수 컬럼 누락 → **Blocked**
- variant 라벨 이상(중복, control/treatment 누락, 2개 초과) → **Blocked**
- 음수/타입 오류/NaN → **Blocked**
- `conversions > users` → **Blocked**
- (옵션) 기간/메타 불일치(예: end < start) → **Blocked**
- (옵션) users가 비정상적으로 작음(예: < 100) → **Warning**(해석 불안정)

---

## 7) Health Check (자동 검증)
### 7.1 SRM (Sample Ratio Mismatch)
- 목적: 기대 트래픽 분배 대비 실제 샘플 비율이 유의하게 다른지 탐지
- 입력:
  - observed: control_users, treatment_users
  - expected split: 기본 50/50, 메타 입력으로 변경 가능(예: 60/40)
- 방법: chi-square goodness-of-fit
- 출력: p-value, observed/expected, 상태 배지
- 기준(기본값):
  - p < 0.001 → **Warning (SRM detected)**
  - p < 0.00001 → **Blocked (Severe SRM)** *(임계값 설정 가능)*

### 7.2 기타 Health Check
- 스키마/타입/논리(6장) 결과를 종합해:
  - **Healthy / Warning / Blocked** 상태 배지
- Blocked이면 이후 분석은 “참고용 미실행” 또는 “메모 결론 Hold”로 고정

---

## 8) Primary 결과 분석 (MVP: 전환율)
### 8.1 계산 항목
- control_rate = conversions_c / users_c
- treatment_rate = conversions_t / users_t
- absolute lift = treatment_rate − control_rate
- relative lift = (treatment_rate / control_rate) − 1
- p-value:
  - 기본: two-proportion z-test (양측)
  - 작은 표본/극단비율 등 조건 미달 시: **Fisher exact test로 대체(권장)**

### 8.2 신뢰구간(95% CI)
- 비율 차이(absolute lift)의 95% CI 제공
- 구현 권장: statsmodels의 검증된 함수를 사용
- 출력: lift, CI lower/upper, p-value, 해석 문구(“유의/비유의”)

---

## 9) Guardrail 비교 (MVP: 비율형)
### 9.1 Guardrail 정의
- 각 guardrail 컬럼 `g`에 대해:
  - g_rate = g / users
  - Δg = treatment_g_rate − control_g_rate
- “악화(worsened)” 정의(기본값, 설정 가능):
  - (1) Δg > 0 AND
  - (2) (Δg > guardrail_abs_threshold) OR (p < 0.05)
  - 예: error_rate가 **+0.10%p** 이상 증가하면 실무적으로 악화로 표시

### 9.2 출력
- 각 guardrail에 대해: control rate, treatment rate, Δ, (선택) p-value, worsened 배지
- Guardrail이 하나라도 worsened면 Decision 단계에서 보수적으로 처리

---

## 10) Decision Framework (Launch/Hold/Rollback)
### 10.1 기본 원칙
- Health Check가 신뢰되지 않으면 결론을 내리지 않는다.
- Primary 개선이 있어도 Guardrail 악화가 크면 안전을 우선한다.

### 10.2 룰 기반 결론 (MVP 기본)
1. **Blocked**(스키마/논리 오류 또는 Severe SRM) → **Hold**
2. **SRM Warning**(p < SRM threshold) → **Hold**
3. Primary 유의(p < 0.05) AND Guardrail worsened 없음 → **Launch**
4. Primary 유의 AND Guardrail worsened 있음 →
   - 악화가 “심각(severe)” 기준 초과 시 **Rollback**
   - 그 외 **Hold**
5. Primary 비유의(p ≥ 0.05) → **Hold**

### 10.3 “심각(severe)” 가드레일 기준(기본값, 설정 가능)
- 예: any guardrail Δg > severe_threshold (예: **+0.30%p**) 이면 Rollback 추천

> 주: Rollback은 “이미 롤아웃된 경우/실험 종료 후 배포 상태”에 따라 의미가 달라질 수 있으므로, Memo에 “현재 배포 상태” 입력 필드를 두거나(메타) 기본 문구를 중립적으로 작성한다(예: “배포 중단/확대 금지 권고”).

---

## 11) Decision Memo (1pager) 산출물 요구사항
### 11.1 포함 섹션 (고정 템플릿)
- Summary: 실험명/기간/변형/Primary/가드레일/데이터 버전
- Decision: Launch / Hold / Rollback (룰 기반) + 한 줄 이유
- Evidence:
  - Health: SRM p-value, 품질 이슈 목록
  - Primary: control/treatment, lift, 95% CI, p-value
  - Guardrails: worsened 리스트와 크기(Δ)
- Risks & Limitations:
  - 집계 기반, 이벤트 다회 카운트 가능성, 작은 표본 경고 등 자동 기입
- Next Actions:
  - Launch 시: 롤아웃 단계/모니터링 guardrail/알림 조건 제안
  - Hold 시: 필요한 추가 샘플/추가 실험/데이터 수정 체크리스트
  - Rollback 시: 즉시 조치 + 원인 분석 항목

### 11.2 Export
- Markdown 다운로드
- HTML 다운로드(공유/Confluence 붙여넣기 용)
- (P1) PDF/Notion 템플릿 최적화

---

## 12) UX / 화면 구성 (Streamlit 멀티페이지)
### 12.1 Home (Experiments List)
- 실험 목록(세션 기반)
- 상태 배지(Healthy/Warning/Blocked)
- 최근 결과 요약(lift, decision)

### 12.2 New Experiment
- CSV 업로드 + 즉시 스키마/논리 검증 결과 표시
- 메타 입력:
  - 실험명, 기간, 가설
  - expected split(기본 50/50)
  - primary metric(고정: conversions/users)
  - guardrail 선택(컬럼 체크박스) + 임계치(기본값 제공)

### 12.3 Results
- Health Check 카드(SRM/품질 이슈)
- Primary 결과 카드(lift/CI/p-value)
- Guardrail 테이블(worsened 배지)

### 12.4 Decision Memo
- 1pager 프리뷰(마크다운 렌더)
- Download: MD/HTML
- “결론이 Hold인 이유”가 상단에 명시되도록 UI 강조

### 12.5 빈 상태/에러 처리(중요)
- 업로드 없이 Results/Decision 진입 시: 친절한 안내 + 업로드 페이지 링크
- Blocked일 때: 무엇이 잘못됐는지(컬럼/행/값) 구체적으로 표시

---

## 13) 기술 스택 / 아키텍처 (MVP)
- UI: Streamlit (multipage)
- 분석: pandas, numpy, scipy, statsmodels
- 저장(MVP): `st.session_state`
- (P1) 저장 확장: SQLite 또는 DuckDB (실험 히스토리/버전 관리)

---

## 14) 프로젝트 구조 (예시)
. ├─ app.py ├─ pages/ │ ├─ 1_Home.py │ ├─ 2_New_Experiment.py │ ├─ 3_Results.py │ └─ 4_Decision_Memo.py ├─ src/experimentos/ │ ├─ init.py │ ├─ healthcheck.py │ ├─ analysis.py │ ├─ memo.py │ ├─ models.py │ ├─ state.py │ ├─ demo_data.py │ └─ logger.py ├─ tests/ └─ requirements.txt


---

## 15) 품질 / 테스트 (MVP 수용기준 포함)
### 15.1 단위 테스트(pytest)
- SRM 탐지:
  - 정상 split → Healthy
  - 심한 불균형 → Warning/Blocked
- 스키마/논리:
  - conversions > users → Blocked
  - variant 누락/중복 → Blocked
- primary 계산:
  - 리턴 dict 키/타입/값 범위 검증
- guardrail:
  - Δ 및 worsened 판정(임계치/유의성 조건)
- decision 룰:
  - 각 분기(Launch/Hold/Rollback) 재현

### 15.2 수용기준(AC)
- 사용자가 sample.csv 업로드 시:
  - Health/Primary/Guardrail/Decision Memo가 한 흐름으로 생성된다.
- SRM Warning 데이터 업로드 시:
  - Decision은 자동으로 Hold이며, Memo에 SRM 근거가 포함된다.
- guardrail 심각 악화 데이터 업로드 시:
  - Primary가 유의해도 Decision은 Hold 또는 Rollback으로 간다(설정 기준에 따라).
- MD/HTML 다운로드 파일이 정상 생성된다.

---

## 16) 데이터/윤리/보안
- 개인정보/회사 기밀 데이터 사용 금지
- 공개 데이터 또는 합성 데이터만 사용
- Memo에 자동으로 “가정/제약(집계 입력, 통계 방법, 임계치)”를 명시

---

## 17) 한계 (Limitations)
- 집계형 입력 기반으로, 코호트/이벤트 레벨 진단은 제한적
- 고급 기법(CUPED/층화/순차검정) 미포함
- 실험 도구(Feature flag/배포)와 직접 연동하지 않음

---

## 18) 로드맵 (Next)
### P1 (V1)
- 실험 히스토리 DB 저장(SQLite/DuckDB)
- Segment breakdown 탭(신규/복귀/헤비 등) — 입력 스키마 확장 필요
- CUPED 또는 층화 중 1개만 선택 적용
- Notion/Confluence export 템플릿 개선, PDF 출력

### P2 (V2)
- 이벤트 레벨 입력 지원 + 코호트 분석
- 순차검정/중간중단 가이드
- 조직 단위 Metric Catalog/정의 거버넌스

---

## 19) 참고(레퍼런스)
- Statsig — Decision Framework
- GrowthBook — SRM/분석 UX
- Eppo — Guardrail/Metric governance
- Optimizely — 운영 UX
- PostHog Experiments — 간단한 플로우 참고