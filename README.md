# ExperimentOS — A/B 실험 의사결정 자동화 플랫폼

A/B 테스트에서 "전환율이 올랐다"는 숫자만 보고 출시하면 위험합니다.
ExperimentOS는 **검증 표준화 + 의사결정 자동화**를 통해 이런 실수를 구조적으로 방지합니다.

```
CSV 업로드 → Health Check (SRM/스키마) → 통계 분석 (z-test/Bayesian)
→ Guardrail 검증 → Launch/Hold/Rollback 의사결정 메모 자동 생성
```

**[Live Demo](https://experimentos-guardrails.vercel.app)** | **[Architecture](./ARCHITECTURE.md)** | **[Design Rationale](./docs/design-rationale.md)**

---

## Analysis Case Studies

### 1. Marketing A/B Test — 588K 유저 HTE 분석

**데이터**: Kaggle Marketing A/B Testing (588,101 users) | **기법**: SRM, z-test, Heterogeneous Treatment Effects, Dose-response

**핵심 발견**: 광고 노출 50회+ 구간에서 전환 효과 급증 (+5.9%p), 200+회에서 포화 현상 발견
**비즈니스 임팩트**: 증분 매출 $217K 추정, Frequency Cap 적용 시 $137K 추가 잠재

[Notebook](./notebooks/case-study-marketing-ab-test.ipynb) | [SQL Version](./notebooks/case-study-marketing-sql-analysis.ipynb)

### 2. Cohort Retention — E-commerce 고객 생존 분석

**데이터**: UCI Online Retail (541K transactions, 4,372 customers) | **기법**: 코호트 리텐션, LTV 추정, 세그먼트 비교

**핵심 발견**: Month 0→1 리텐션 드랍이 가장 급격, 3개월 생존 고객은 장기 고객으로 안정화
**비즈니스 임팩트**: CRM 개입 최적 타이밍(1개월 내) 및 UK vs Non-UK 리텐션 차이 정량화

[Notebook](./notebooks/case-study-cohort-retention.ipynb)

### 3. Funnel Analysis — 전환 병목 진단

**데이터**: eCommerce Events (Cosmetics Shop) | **기법**: 유저 퍼널, 카테고리별 비교, 가격 민감도

**핵심 발견**: View→Cart 단계가 최대 병목, 고가 상품($50+)에서 Cart Abandonment 급증
**비즈니스 임팩트**: Cart Abandonment 10% 회복 시 추가 매출 기회 추정

[Notebook](./notebooks/case-study-funnel-analysis.ipynb)

### 4. SRM False Positive Detection — 거짓 양성 사례

**데이터**: 시뮬레이션 (봇 트래픽 오염) | **기법**: SRM, 일별 트래픽 분석, 데이터 정제

**핵심 발견**: 전환율 +26% → 봇 트래픽 격리 후 +0.2%p (n.s.), 결론 완전 뒤집힘

[Notebook](./notebooks/case-study-srm-detection.ipynb)

### 5. Sequential Testing — Monte Carlo 시뮬레이션

**데이터**: 60,000회 시뮬레이션 | **기법**: O'Brien-Fleming vs Pocock alpha spending

**핵심 발견**: OBF Type I=0.033, Power(+1%p)=0.998 / Pocock Savings(+2%p)=79.6%

[Notebook](./notebooks/simulation-sequential-boundaries.ipynb)

---

## 핵심 역량

| 분야 | 기법 | 활용 |
|------|------|------|
| **A/B 테스트** | SRM, z-test, chi-square, Bayesian, Sequential Testing | 실험 설계 → 검증 → 의사결정 전 과정 |
| **세그먼트 분석** | HTE, 코호트 리텐션, 퍼널 분석, Dose-response | 전체 평균이 숨기는 패턴 발견 |
| **SQL** | CTE, Window Functions, Self-JOIN, CASE WHEN, UNION ALL | [9개 쿼리 패턴 시연](./notebooks/case-study-marketing-sql-analysis.ipynb) |
| **통계** | 다중비교 보정, O'Brien-Fleming boundary, Beta-Binomial | 학술 근거 기반 임계값 설정 ([Design Rationale](./docs/design-rationale.md)) |
| **시각화** | matplotlib, seaborn, Recharts | 히트맵, Forest Plot, Dose-response curve |
| **비즈니스 연결** | 증분 매출, LTV, Cart Abandonment → ROI | 모든 분석에 매출 임팩트 포함 |

---

## Evidence

| 항목 | 수치 |
|------|------|
| Unit Tests | 209 passing (27 test files) |
| Core Logic | 3,700+ lines Python (scipy/statsmodels) |
| Frontend | 7,200+ lines TypeScript (React 19) |
| Decision Regression | 2개 전용 테스트 파일 (절대 깨뜨리지 않음) |
| Case Studies | 5개 분석 노트북 (실데이터 + 시뮬레이션) |
| Design Rationale | [Threshold 선택 근거 (7개 학술 참고문헌)](./docs/design-rationale.md) |

---

## Key Analysis Capabilities

### 1. SRM(Sample Ratio Mismatch) 탐지

실험 데이터의 품질을 분석 전에 검증합니다. Chi-square 검정으로 트래픽 분배 이상을 탐지하며,
임계값은 Microsoft ExP 플랫폼 기준(p < 0.001 Warning, p < 0.00001 Blocked)을 따릅니다.

### 2. Multi-variant 분석 (N-variant)

3개 이상 variant 비교 시 다중 비교 문제를 자동 처리합니다.
Overall chi-square → 쌍별 z-test → p-value 보정 (Bonferroni/Holm/FDR_BH)

### 3. Guardrail 이중 안전장치

Primary metric이 유의하더라도 부작용 지표의 악화를 감지하면 Launch를 차단합니다.

### 4. Sequential Testing (조기 종료)

O'Brien-Fleming alpha spending function으로 실험 기간 중 조기 종료 가능 여부를 판정합니다.

### 5. 규칙 기반 의사결정

```
Health Check Blocked → Hold (데이터 문제 우선 해결)
SRM Warning         → Hold (트래픽 이상 조사)
Primary 유의 + Severe Guardrail → Rollback
Primary 유의 + Guardrail 정상   → Launch
Primary 비유의                   → Hold
```

> Bayesian 분석(P(B>A), Expected Loss)은 **설명용**으로만 제공합니다.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend (Web)** | React 19 + TypeScript 5.8 + Tailwind CSS v4 + Vite 6 + Recharts 3 |
| **Frontend (Local)** | Streamlit (멀티페이지) |
| **Backend API** | FastAPI + Uvicorn |
| **Analysis** | pandas, numpy, scipy, statsmodels |
| **Deploy** | Vercel (frontend) + Render (backend) |

---

## Quickstart

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend
cd experimentos-guardrails
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

<details>
<summary>Streamlit (로컬 분석용)</summary>

```bash
pip install -r requirements.txt
streamlit run app.py
```
</details>

---

<details>
<summary>API Endpoints</summary>

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/health-check` | CSV 스키마 검증 + SRM 체크 |
| `POST` | `/api/analyze` | Primary + Guardrail 분석 |
| `POST` | `/api/continuous-metrics` | 연속형 지표 분석 |
| `POST` | `/api/bayesian-analysis` | 베이지안 분석 |
| `POST` | `/api/decision-memo` | Decision Memo 생성 |
| `POST` | `/api/sequential-analysis` | Sequential 분석 |
| `GET` | `/api/sequential-boundaries` | Sequential boundary 계산 |

</details>

<details>
<summary>Input Data Format</summary>

**필수 컬럼**: `variant`, `users`, `conversions`

```csv
variant,users,conversions,guardrail_cancel,guardrail_error
control,10000,1200,120,35
treatment,10050,1320,118,33
```

</details>

<details>
<summary>Tests (209 passing)</summary>

```bash
python -m pytest tests/ -v
```

| 카테고리 | 테스트 파일 | 설명 |
|---------|-----------|------|
| Decision Regression | `test_decision.py`, `test_decision_branches.py` | 의사결정 회귀 |
| Sequential | `test_sequential.py`, `test_sequential_boundaries.py` | 57 tests |
| Multi-variant | `test_multivariant_*.py` | 21 tests |
| Analysis | `test_analysis.py`, `test_multiple_comparisons.py` | 핵심 분석 로직 |

</details>

<details>
<summary>Deployment</summary>

- **Frontend**: Vercel (`experimentos-guardrails/`)
- **Backend**: Render (GitHub main push → auto-deploy)
- **Docker**: `docker build -t experimentos-api . && docker run -p 8000:8000 experimentos-api`

</details>

---

## License

MIT
