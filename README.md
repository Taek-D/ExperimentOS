# ExperimentOS — A/B 실험 검증 및 의사결정 자동화

실험(A/B) 데이터를 넣으면 **SRM/효과(신뢰구간)/가드레일**을 자동 검증하고,
**Launch/Hold/Rollback 결정 메모(1pager)**를 생성해 실험 의사결정 속도와 일관성을 높이는 플랫폼입니다.

> 이 프로젝트는 Hackle/Statsig/GrowthBook 같은 **실험 실행 플랫폼(Feature Flag/SDK/트래킹)**을 대체하지 않습니다.
> 어떤 실험 도구에서든 뽑을 수 있는 "결과 데이터"를 입력으로 받아, **검증 표준화 + 결정 메모 자동화**를 제공하는 **Decision Layer**입니다.

**[Architecture Documentation](./ARCHITECTURE.md)** — Tech stack, folder structure, coding conventions, and how to extend the system.

---

## Live Demo

- **Frontend (React)**: [https://experimentos-guardrails.vercel.app](https://experimentos-guardrails.vercel.app)
- **Backend (FastAPI)**: [https://experimentos-api.onrender.com](https://experimentos-api.onrender.com)

> Render 무료 티어는 15분 비활성 후 슬립 모드로 전환됩니다. 첫 요청 시 약 30-60초 정도 웜업 시간이 필요합니다.

---

## Why (Problem)

실험 결과 공유 방식이 매번 달라서,
- SRM(표본 불균형)이나 가드레일 악화를 놓치고 "좋아 보이는 숫자"로 잘못 롤아웃할 수 있고
- 리뷰/검토가 반복되며 의사결정이 느려지는 문제가 생깁니다.

ExperimentOS는 **실험 운영의 표준(Health Check → Result → Decision Memo)**을 자동화해
스쿼드가 빠르게 같은 결론에 도달하도록 돕습니다.

---

## Target Users

- **데이터 분석가(Primary)**: 실험 검증/리포트/결정 메모를 표준화해 리드타임을 줄이고 싶다.
- **PM/PO(Decision Maker)**: 통계 설명보다 "결론 + 근거 + 리스크 + 다음 액션"이 한 장으로 필요하다.
- **엔지니어/실험 운영 담당(Secondary)**: 롤아웃/롤백 판단 기준이 명확한 메모를 받아 실행하고 싶다.

---

## Features

1. **CSV 업로드 + 스키마 검증**
   - 필수: `variant(control/treatment)`, `users`, `conversions`
   - 논리 검증: `conversions <= users`, 음수 금지 등

2. **Health Check 자동화**
   - SRM(chi-square) 자동 탐지 (기대 split 기본 50/50, 설정 가능)
   - 결측/중복/라벨/타입 오류 체크
   - 상태 배지: **Healthy / Warning / Blocked**

3. **Primary 결과 분석 (전환율)**
   - conversion_rate 기반 `lift(절대/상대)`, `95% CI`, `p-value`
   - 기본 검정: two-proportion z-test (양측)
   - 연속형 지표(매출, 체류시간 등) 지원 (Welch's t-test)
   - 베이지안 분석(Beta-Binomial/Posterior Simulation) 참고용 제공

4. **Guardrail 비교**
   - 선택한 guardrail 컬럼(control vs treatment) 비교
   - 악화(worsened) / 심각한 악화(severe) 배지 표시

5. **Decision Memo 1pager 자동 생성 + Export**
   - 결론: Launch/Hold/Rollback (룰 기반)
   - 근거/리스크/Next Actions 포함
   - Markdown/HTML 다운로드

6. **Experiment Planning**
   - Experiment Charter: 가설 및 Primary Metric 사전 정의
   - Power Calculator: 목표 표본 크기 및 예상 기간 산출

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend (Web)** | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| **Frontend (Local)** | Streamlit (멀티페이지) |
| **Backend API** | FastAPI + Uvicorn |
| **Analysis** | pandas, numpy, scipy, statsmodels |
| **Frontend Hosting** | Vercel |
| **Backend Hosting** | Render (Free Tier) |

---

## Project Structure

```
.
├── experimentos-guardrails/       # React Frontend (Vercel 배포)
│   ├── api/client.ts              # API client
│   ├── components/                # React 컴포넌트
│   ├── App.tsx                    # 메인 앱
│   ├── vercel.json                # Vercel 배포 설정
│   └── .env.production            # 프로덕션 API URL
│
├── backend/
│   └── main.py                    # FastAPI 서버
│
├── src/experimentos/              # 핵심 분석 로직 (공유)
│   ├── config.py                  # 통합 설정 (Thresholds)
│   ├── healthcheck.py             # 스키마 검증 & SRM 탐지
│   ├── analysis.py                # Primary & Guardrail 분석
│   ├── continuous_analysis.py     # 연속형 지표 분석 (Welch's t-test)
│   ├── bayesian.py                # 베이지안 분석
│   ├── power.py                   # Power Calculator
│   ├── memo.py                    # Decision 룰 엔진 & Memo 생성
│   └── state.py                   # Session state 관리
│
├── pages/                         # Streamlit 페이지 (로컬용)
│   ├── 1_Home.py
│   ├── 2_New_Experiment.py
│   ├── 3_Results.py
│   └── 4_Decision_Memo.py
│
├── tests/                         # pytest 테스트 스위트
├── .tmp/                          # 샘플 CSV 파일
├── app.py                         # Streamlit 엔트리 포인트
├── Dockerfile                     # Docker 빌드 설정
├── render.yaml                    # Render 배포 설정
└── requirements.txt               # Python 의존성
```

---

## Quickstart

### Option A: React + FastAPI (프로덕션 아키텍처)

**Backend:**
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd experimentos-guardrails
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

### Option B: Streamlit (로컬 분석용)

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## Input Data Format (CSV)

### 필수 컬럼
- **variant**: `control` 또는 `treatment` (2개 variant만 지원)
- **users**: 각 variant 유저 수 (int, > 0)
- **conversions**: 전환 수 (int, 0 이상, users 이하)

### 옵션 컬럼
- **Guardrails**: `guardrail_cancel`, `guardrail_refund` 등 (카운트형)
- **연속형 지표**: `revenue_sum`, `revenue_sum_sq` 쌍으로 제공

### 예시
```csv
variant,users,conversions,guardrail_cancel,guardrail_error
control,10000,1200,120,35
treatment,10050,1320,118,33
```

샘플 CSV 파일은 `.tmp/` 디렉토리에 포함되어 있습니다.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API 상태 확인 |
| `POST` | `/api/health-check` | CSV 스키마 검증 + SRM 체크 |
| `POST` | `/api/analyze` | Primary + Guardrail 분석 |
| `POST` | `/api/continuous-metrics` | 연속형 지표 분석 (Welch's t-test) |
| `POST` | `/api/bayesian-analysis` | 베이지안 분석 |
| `POST` | `/api/decision-memo` | Decision Memo 생성 |

모든 파일 업로드 엔드포인트는 `multipart/form-data`로 CSV 파일을 전송합니다.

---

## Configuration

`src/experimentos/config.py`에서 주요 설정을 관리합니다:

```python
SRM_WARNING_THRESHOLD = 0.001       # p < 0.001 → Warning
SRM_BLOCKED_THRESHOLD = 0.00001     # p < 0.00001 → Blocked
GUARDRAIL_WORSENED_THRESHOLD = 0.001 # Δ >= 0.1%p
GUARDRAIL_SEVERE_THRESHOLD = 0.003   # Δ >= 0.3%p
SIGNIFICANCE_ALPHA = 0.05
```

---

## Decision Rules

1. **Blocked** (스키마/논리 오류) → **Hold**
2. **SRM 경고** → **Hold**
3. **Primary 유의** + **Severe Guardrail 악화** → **Rollback**
4. **Primary 유의** + **일반 Guardrail 악화** → **Hold**
5. **Primary 유의** + **Guardrail 정상** → **Launch**
6. **Primary 비유의** → **Hold**

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## Deployment

### Frontend (Vercel)
```bash
cd experimentos-guardrails
vercel --prod
```

### Backend (Render)
GitHub main 브랜치에 push하면 자동 배포됩니다. 설정은 `render.yaml` 참조.

### Docker (로컬)
```bash
docker build -t experimentos-api .
docker run -p 8000:8000 experimentos-api
```

---

## License

MIT
