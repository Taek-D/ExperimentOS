# ExperimentOS — A/B 실험 의사결정 자동화 플랫폼

## 이 프로젝트가 해결하는 문제

A/B 테스트에서 "전환율이 올랐다"는 숫자만 보고 출시하면 위험합니다.

실제 사례: 전환율 +26% 상대 상승을 보인 결제 페이지 리디자인 실험에서,
**SRM 탐지 → 일별 트래픽 분석 → 봇 트래픽 격리**를 수행하자
효과가 +0.2%p (n.s.)로 감소하며 결론이 뒤집혔습니다.
([Case Study: SRM이 숨긴 거짓 양성](./notebooks/case-study-srm-detection.ipynb))

ExperimentOS는 이런 실수를 **구조적으로** 방지합니다:

```
CSV 업로드 → Health Check (SRM/스키마) → 통계 분석 (z-test/Bayesian)
→ Guardrail 검증 → Launch/Hold/Rollback 의사결정 메모 자동 생성
```

> 이 프로젝트는 Hackle/Statsig/GrowthBook 같은 실험 실행 플랫폼을 대체하지 않습니다.
> 어떤 도구에서든 뽑을 수 있는 "결과 데이터"를 입력으로 받아,
> **검증 표준화 + 의사결정 자동화**를 제공하는 **Decision Layer**입니다.

**[Live Demo](https://experimentos-guardrails.vercel.app)** | **[Architecture](./ARCHITECTURE.md)** | **[Design Rationale](./docs/design-rationale.md)**

---

## Key Analysis Capabilities

### 1. SRM(Sample Ratio Mismatch) 탐지

실험 데이터의 품질을 분석 전에 검증합니다. Chi-square 검정으로 트래픽 분배 이상을 탐지하며,
임계값은 Microsoft ExP 플랫폼 기준(p < 0.001 Warning, p < 0.00001 Blocked)을 따릅니다.

- 왜 α=0.05가 아닌 0.001인가? → SRM은 실험의 내적 타당성(internal validity) 판단이므로, false alarm 비용이 높습니다
- 자세한 근거: [Design Rationale](./docs/design-rationale.md#1-srm-detection-thresholds)

### 2. Multi-variant 분석 (N-variant)

3개 이상 variant 비교 시 다중 비교 문제(multiple comparisons problem)를 자동 처리합니다.

- Overall chi-square → 쌍별 z-test → p-value 보정 (Bonferroni/Holm/FDR_BH)
- 기본 Bonferroni를 선택한 이유: 비전문가에게 설명 가능성이 가장 높음
- Best variant 자동 선정 (보정된 p-value 기준)

### 3. Guardrail 이중 안전장치

Primary metric이 유의하더라도 부작용 지표(취소율, 오류율 등)의 악화를 감지하면 Launch를 차단합니다.
이는 "국소 최적화(local optimization)" 방지를 위한 설계입니다.

- Worsened: Δ >= 0.1%p (기저율 1% 대비 ~10% 상대 악화)
- Severe: Δ >= 0.3%p (기저율 1% 대비 ~30% 상대 악화 → 자동 차단)

### 4. Sequential Testing (조기 종료)

O'Brien-Fleming alpha spending function으로 실험 기간 중 조기 종료 가능 여부를 판정합니다.
5회 중간 분석(20/40/60/80/100%)을 기본으로 하며, 초기에 보수적 boundary를 적용하여 성급한 종료를 방지합니다.

### 5. 규칙 기반 의사결정 (Human Judgment 보조)

```
Health Check Blocked → Hold (데이터 문제 우선 해결)
SRM Warning         → Hold (트래픽 이상 조사)
Primary 유의 + Severe Guardrail → Rollback
Primary 유의 + Guardrail 정상   → Launch
Primary 비유의                   → Hold
```

> Bayesian 분석(P(B>A), Expected Loss)은 **설명용**으로만 제공합니다.
> 의사결정은 빈도론적 분석 + guardrail에만 의존합니다.

---

## Evidence

| 항목 | 수치 |
|------|------|
| Unit Tests | 209 passing (27 test files) |
| Core Logic | 3,700+ lines Python (scipy/statsmodels) |
| Frontend | 7,200+ lines TypeScript (React 19) |
| Decision Regression | 2개 전용 테스트 파일 (절대 깨뜨리지 않음) |
| Case Study | [SRM False Positive Detection](./notebooks/case-study-srm-detection.ipynb) |
| Case Study | [Marketing A/B Test — 588K 실데이터 HTE 분석](./notebooks/case-study-marketing-ab-test.ipynb) |
| SQL Analysis | [동일 데이터 SQL(DuckDB) 분석 — 9개 쿼리 패턴](./notebooks/case-study-marketing-sql-analysis.ipynb) |
| Simulation | [OBF vs Pocock — 60,000 Monte Carlo](./notebooks/simulation-sequential-boundaries.ipynb) |
| Design Rationale | [Threshold 선택 근거 (7개 학술 참고문헌)](./docs/design-rationale.md) |

---

## Target Users

| Persona | 역할 | 니즈 |
|---------|------|------|
| **데이터 분석가** | Primary | 검증/리포트/결정 메모 표준화로 리드타임 단축 |
| **PM/PO** | Decision Maker | 결론 + 근거 + 리스크 + 다음 액션을 한 장으로 파악 |
| **엔지니어** | Secondary | 롤아웃/롤백 판단 기준이 명확한 메모 수령 |

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

## Features

1. **CSV 업로드 + 스키마 검증** — 필수 컬럼(`variant`, `users`, `conversions`), 논리 검증
2. **Health Check** — SRM 탐지(N-variant), 결측/중복/타입 오류 체크, Healthy/Warning/Blocked
3. **Primary 분석** — 2-variant z-test, Multi-variant chi-square + 쌍별 비교, 연속형 Welch's t-test
4. **Guardrail 비교** — 2-variant/Multi-variant, worsened/severe 자동 감지
5. **Decision Memo** — Launch/Hold/Rollback 1-pager, Markdown/HTML 다운로드
6. **Sequential Testing** — O'Brien-Fleming boundary, 조기 종료 판정, Boundary 시각화
7. **Experiment Planning** — Power Calculator, Experiment Charter
8. **외부 플랫폼 연동** — Statsig/GrowthBook/Hackle, Auto-sync, registry 패턴
9. **베이지안 분석** — P(B>A), Expected Loss, posterior simulation (설명용)
10. **시각화** — Forest Plot, Posterior Distribution, Power Curve, Boundary Chart
11. **UX** — Guided Tour, Glossary Tooltips, Demo Data

---

## Quickstart

### React + FastAPI

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

### Streamlit (로컬 분석용)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Input Data Format

### 필수 컬럼
- **variant**: `control`/`treatment` (2-variant) 또는 `control`/`variant_a`/`variant_b` (Multi-variant)
- **users**: 각 variant 유저 수 (int, > 0)
- **conversions**: 전환 수 (int, 0 이상, users 이하)

### 옵션 컬럼
- Guardrails: `guardrail_cancel`, `guardrail_error` 등 (카운트형)
- 연속형 지표: `revenue_sum`, `revenue_sum_sq` 쌍

### 예시

```csv
variant,users,conversions,guardrail_cancel,guardrail_error
control,10000,1200,120,35
treatment,10050,1320,118,33
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/health-check` | CSV 스키마 검증 + SRM 체크 |
| `POST` | `/api/analyze` | Primary + Guardrail 분석 |
| `POST` | `/api/continuous-metrics` | 연속형 지표 분석 |
| `POST` | `/api/bayesian-analysis` | 베이지안 분석 |
| `POST` | `/api/decision-memo` | Decision Memo 생성 |
| `POST` | `/api/sequential-analysis` | Sequential 분석 |
| `GET` | `/api/sequential-boundaries` | Sequential boundary 계산 |

---

## Tests

```bash
python -m pytest tests/ -v  # 209 tests
```

| 카테고리 | 테스트 파일 | 설명 |
|---------|-----------|------|
| **Decision Regression** | `test_decision.py`, `test_decision_branches.py` | 의사결정 회귀 (절대 불변) |
| **Sequential** | `test_sequential.py`, `test_sequential_boundaries.py` | Sequential testing (57 tests) |
| **Multi-variant** | `test_multivariant_*.py` | N-variant 분석/의사결정 (21 tests) |
| **Analysis** | `test_analysis.py`, `test_multiple_comparisons.py` | 핵심 분석 로직 |
| **Integrations** | `test_integrations.py`, `test_*_provider*.py` | 외부 플랫폼 연동 |

---

## Deployment

- **Frontend**: Vercel (`experimentos-guardrails/`)
- **Backend**: Render (GitHub main push → auto-deploy)
- **Docker**: `docker build -t experimentos-api . && docker run -p 8000:8000 experimentos-api`

---

## License

MIT
