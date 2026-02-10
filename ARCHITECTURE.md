# ExperimentOS Architecture

> This document is the **single source of truth** for ExperimentOS structure, conventions, and extension points.
> Last updated: 2026-02-11

## 1. Tech Stack

### Core Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13+ | Core language (modern type hints, stdlib improvements) |
| **FastAPI** | 0.115+ | Backend API server (REST endpoints, file uploads) |
| **React** | 19 | Frontend web application |
| **TypeScript** | 5.8 | Type-safe frontend (strict mode) |
| **Tailwind CSS** | v4 | Utility-first CSS framework |
| **Vite** | 6.4+ | Frontend build tool |
| **Streamlit** | 1.29+ | Local analysis UI (multi-page apps) |
| **pandas** | 2.2+ | Data manipulation (CSV handling, DataFrame operations) |
| **numpy** | 2.0+ | Numeric primitives (vectorized math, RNG for simulation) |
| **scipy** | 1.11+ | Statistical tests (chi-square, z-test) |
| **statsmodels** | 0.14+ | Statistical models (proportions z-test, CIs, power calcs) |
| **markdown** | 3.5+ | Markdown to HTML conversion for export |
| **pytest** | 8+ | Unit tests (`pytest -v`) |

### Why These Choices?
- **FastAPI + React**: Production-grade separation of concerns; typed API contracts.
- **scipy + statsmodels**: battle-tested A/B building blocks (SRM, z-test, CIs, power).
- **numpy RNG**: deterministic Bayesian simulations in tests via fixed seeds.
- **TypeScript strict mode**: compile-time safety for union types (2-variant vs multi-variant).

---

## 2. Folder Structure

```
.
├── backend/                        # FastAPI API server
│   ├── main.py                     # Entry point, CORS, variant auto-detection, endpoints
│   ├── utils.py                    # Utility functions
│   └── routers/
│       └── integrations.py         # Integration endpoints (/integrations/{provider}/...)
│
├── src/experimentos/               # Business logic (stateless & testable)
│   ├── __init__.py
│   ├── config.py                   # Centralized thresholds & numeric tolerances
│   ├── state.py                    # Session state initialization & helpers
│   ├── logger.py                   # Centralized logging setup
│   ├── healthcheck.py              # Schema validation, SRM detection (N-variant)
│   ├── analysis.py                 # Orchestrator: conversion + guardrails + multi-variant
│   ├── continuous_analysis.py      # Welch t-test from sufficient statistics
│   ├── bayesian.py                 # Beta-Binomial + continuous posterior (multi-variant)
│   ├── power.py                    # Sample size / power calculator utilities
│   ├── memo.py                     # Decision rules + memo generation (multi-variant)
│   ├── sequential.py               # Sequential testing (O'Brien-Fleming alpha spending)
│   └── integrations/               # External platform integrations
│       ├── base.py                 # Base provider interface
│       ├── registry.py             # Provider registry
│       ├── schema.py               # Integration schemas
│       ├── statsig.py              # Statsig provider
│       ├── growthbook.py           # GrowthBook provider
│       ├── hackle.py               # Hackle provider
│       ├── dummy.py                # Dummy provider (testing)
│       ├── cache.py                # Cache layer
│       ├── retry.py                # Retry logic
│       └── transform.py            # Data transformation
│
├── experimentos-guardrails/        # React frontend (Vercel)
│   ├── App.tsx                     # Main app & routing
│   ├── index.tsx                   # Entry point
│   ├── api/client.ts              # Axios API client + type definitions
│   ├── components/                # React components (13)
│   │   ├── Dashboard.tsx          # Result dashboard (multi-variant branching)
│   │   ├── MetricsTable.tsx       # Metrics table (corrected P-value column)
│   │   ├── BayesianInsights.tsx   # Bayesian analysis view (multi-variant)
│   │   ├── ContinuousMetrics.tsx  # Continuous metrics display
│   │   ├── DecisionMemo.tsx       # Decision memo generation
│   │   ├── ExperimentMetadata.tsx # Experiment charter inputs
│   │   ├── ExperimentSelector.tsx # Integration experiment selector
│   │   ├── FileUpload.tsx         # CSV file upload
│   │   ├── Icon.tsx               # Material icon wrapper
│   │   ├── IntegrationConnect.tsx # Integration connection UI
│   │   ├── PowerCalculator.tsx    # Power calculator
│   │   ├── StatsCard.tsx          # Stats summary cards
│   │   ├── TourOverlay.tsx        # Guided tour overlay
│   │   ├── SequentialMonitor.tsx  # Sequential testing monitor
│   │   └── charts/
│   │       ├── ForestPlot.tsx     # Forest plot (multi-variant points)
│   │       ├── BoundaryChart.tsx  # Sequential boundary visualization
│   │       └── chartTheme.ts      # Chart colors + VARIANT_COLORS palette
│   ├── data/demoData.ts           # Demo data (2-variant + multi-variant)
│   ├── hooks/useTour.ts           # Tour state management hook
│   ├── vite.config.ts             # Vite config
│   ├── tsconfig.json              # TypeScript config (strict mode)
│   └── eslint.config.js           # ESLint config
│
├── pages/                          # Streamlit multi-page apps
│   ├── 1_Home.py
│   ├── 2_New_Experiment.py
│   ├── 3_Results.py
│   └── 4_Decision_Memo.py
│
├── tests/                          # Unit tests (209 tests)
│   ├── test_decision.py            # Decision regression (never break)
│   ├── test_decision_branches.py   # Decision branching regression
│   ├── test_analysis.py            # Core analysis tests
│   ├── test_analysis_multivariant_overall.py  # Multi-variant chi-square
│   ├── test_multivariant_guardrails.py        # Multi-variant guardrails
│   ├── test_multivariant_bayesian.py          # Multi-variant Bayesian
│   ├── test_multivariant_decision.py          # Multi-variant decisions
│   ├── test_sequential.py          # Sequential testing (36 tests)
│   ├── test_sequential_boundaries.py # Sequential boundaries (21 tests)
│   └── ...                         # healthcheck, bayesian, continuous, power, etc.
│
├── notebooks/                      # Jupyter notebooks (case studies & simulations)
│   ├── case-study-marketing-ab-test.ipynb     # 588K real data HTE analysis
│   ├── case-study-marketing-sql-analysis.ipynb # SQL(DuckDB) analysis patterns
│   ├── case-study-srm-detection.ipynb         # SRM false positive detection
│   └── simulation-sequential-boundaries.ipynb # OBF vs Pocock Monte Carlo
│
├── app.py                          # Streamlit entry point
├── generate_demo_csvs.py           # Sample CSV generator
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker build config
├── render.yaml                     # Render deployment config
└── .env.example                    # Environment variables template
```

### Folder Responsibilities
- **`backend/`**: FastAPI API layer. Variant auto-detection, multi-variant routing, calls `src/experimentos/*`.
- **`src/experimentos/`**: domain logic. Prefer *pure functions* with explicit inputs/outputs.
- **`experimentos-guardrails/`**: React frontend. TypeScript union types + type guards for 2-variant / multi-variant branching.
- **`pages/`**: Streamlit UI layer only. Read/write `st.session_state`, call `src/experimentos/*`.
- **`tests/`**: unit tests + decision-regression invariants.

---

### CSV Schema Contracts (Required / Optional)

ExperimentOS supports both **2-variant** and **N-variant** (multi-variant) experiment summaries.

#### Variant auto-detection
- 2 variants with `treatment` name → **2-variant mode** (existing code path)
- 3+ variants OR no `treatment` name → **Multi-variant mode** (chi-square + pairwise comparisons)

#### Required columns (always)
- `variant`: variant identifier (`"control"` required; others flexible)
- `users`: unique users exposed to the variant (non-negative int)
- `conversions`: number of users who converted (0 <= conversions <= users)

#### Optional continuous metric columns (sufficient statistics)
Continuous metrics must be provided as **sufficient statistics** per variant:
- `metric_sum`: sum of values
- `metric_sum_sq`: sum of squared values
- `n`: number of observations (defaults to `users`)

#### Healthcheck validation rules
- Basic: `variant` must contain `control`, `users > 0`, `0 <= conversions <= users`
- SRM: chi-square test on user counts vs expected split (supports N-variant uniform split)
- Continuous: completeness, n >= 2, second moment constraint

---

## 3. Multi-Variant Architecture

### Data Flow
```
CSV Upload (variant auto-detection)
    ↓
_is_multivariant(df)  →  True: multi-variant path  /  False: 2-variant path
    ↓
healthcheck.py  (SRM with N-variant uniform split)
    ↓
analysis.py
    2-variant: calculate_primary() + calculate_guardrails()
    N-variant: analyze_multivariant() + calculate_guardrails_multivariant()
    ↓
bayesian.py
    2-variant: calculate_beta_binomial()
    N-variant: calculate_beta_binomial_multivariant()
    ↓
memo.py
    2-variant: make_decision(primary, guardrails)
    N-variant: _make_decision_multivariant(primary, guardrails)
    ↓
sequential.py (optional: interim analysis)
    alpha_spending() → calculate_boundaries() → check_sequential()
    ↓
Frontend (TypeScript union types + type guards)
    isMultiVariantPrimary(r) → MultiVariantPrimaryResult
    isMultiVariantGuardrails(r) → MultiVariantGuardrailResults
    isMultiVariantBayesian(r) → MultiVariantBayesianInsights
```

### Multi-Variant Primary Analysis
- **Overall test**: Chi-square test of independence across all variants
- **Pairwise comparisons**: Each treatment variant vs control (two-proportion z-test)
- **P-value correction**: Configurable method (`holm`, `bonferroni`, `fdr_bh`)
- **Best variant**: Selected by highest significant lift (corrected p-value < alpha)

### Multi-Variant Guardrails
- Each treatment variant compared independently to control
- Per-variant worsened/severe flags
- Summary table: worst variant per guardrail metric

### Multi-Variant Bayesian
- P(variant > control) for each treatment variant
- P(being best) across all variants including control
- Expected loss per variant

### Frontend Type System
```typescript
type PrimaryResultUnion = PrimaryResult | MultiVariantPrimaryResult;
type GuardrailResultUnion = GuardrailResult[] | MultiVariantGuardrailResults;
type BayesianInsightsUnion = BayesianInsights | MultiVariantBayesianInsights;

// Type guards for runtime branching
function isMultiVariantPrimary(r): r is MultiVariantPrimaryResult
function isMultiVariantGuardrails(r): r is MultiVariantGuardrailResults
function isMultiVariantBayesian(r): r is MultiVariantBayesianInsights
```

---

## 4. Coding Conventions

### Formatting
- **Line length**: 100 characters max
- **Indentation**: 4 spaces
- **Imports**: stdlib -> third-party -> local; sorted alphabetically

### Naming
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Classes**: `PascalCase` (rare; prefer functions for MVP)

### Type Hints (Python 3.13+)
Use **built-in generics** (PEP 585) to match the Python version constraint.

```python
def run_health_check(df: pd.DataFrame, expected_split: tuple[float, float]) -> dict[str, object]:
    ...
```

Guidelines:
- All public functions must have type hints.
- Use `dict[str, ...]`, `list[...]`, `tuple[...]` rather than `typing.Dict/List`.
- Keep return values JSON-serializable where possible (dict/list/str/float/bool).

### Error Handling & Status Policy
- Prefer returning structured status (`Healthy/Warning/Blocked`) over raising exceptions for data issues.
- Catch specific exceptions; log with context.

### Numerical Stability & Randomness
- Use tolerances from `config.py` (no magic numbers scattered in modules).
- Bayesian simulations: use `numpy.random.default_rng(seed)`, tests fix seed to avoid flakes.

---

## 5. Decision Logic Module Boundaries

### Separation Principle
Each module has a single responsibility and minimal side effects (logging only).

```
CSV Upload (UI / API)
    ↓
healthcheck.py
    → {overall_status: Healthy/Warning/Blocked, issues: [...], srm: {...}}
    ↓
analysis.py (orchestrator)
    → 2-variant: {primary: {...}, guardrails: [...], continuous?: {...}, bayesian?: {...}}
    → N-variant: {primary: {is_multivariant: true, overall, variants, best_variant}, guardrails: {by_variant, summary}}
    ↓
memo.py
    make_decision(health, primary, guardrails)  # Auto-dispatches 2-variant vs N-variant
    generate_memo(...)
    ↓
Decision Memo UI (Download MD/HTML)
```

### Core rule: Decision is frequentist/guardrail-driven
- `make_decision()` uses **healthcheck + frequentist primary + guardrails** only.
- Bayesian outputs are **explanatory**: displayed in Results, summarized in Memo, never used to switch Launch/Hold/Rollback.

---

## 6. Testing Strategy

### Test Layers
1) **Decision regression (must not change)**
   - `test_decision.py` and `test_decision_branches.py` must remain stable.
   - Any new feature must not alter decision branching for 2-variant cases.

2) **Multi-variant tests**
   - `test_multivariant_guardrails.py`: per-variant guardrail calculations
   - `test_multivariant_bayesian.py`: multi-variant Bayesian analysis
   - `test_multivariant_decision.py`: multi-variant decision rules (5 cases + memo generation)
   - `test_analysis_multivariant_overall.py`: chi-square overall test

3) **Sequential testing tests**
   - `test_sequential.py`: alpha spending, boundaries, sequential check (36 tests)
   - `test_sequential_boundaries.py`: boundary API, edge cases (21 tests)

5) **Unit tests for math modules**
   - `test_continuous_analysis.py`: Welch + CI + edge cases
   - `test_bayesian.py`: smoke + deterministic seed checks
   - `test_power.py`: monotonicity, ratio smoke

6) **Healthcheck schema tests**
   - Missing columns, partial variant completeness, continuous constraints

### Determinism Rules (for Bayesian tests)
- Fix RNG seed in config and in tests.
- Avoid assertions that are too tight; prefer monotonic or threshold assertions.

### Running Tests
```bash
python -m pytest tests/ -v          # All 209 tests
python -m pytest tests/test_multivariant_*.py -v  # Multi-variant only
python -m pytest tests/test_sequential*.py -v     # Sequential testing only
```

---

## 7. Extension Points

### Adding a New Variant Analysis Method
1. Implement in `src/experimentos/analysis.py` (new function)
2. Wire in `backend/main.py` (add detection + routing)
3. Add TypeScript types in `api/client.ts` + type guard
4. Branch UI components using type guard
5. Add tests (never break existing decision tests)

### Adding a New Integration Provider
1. Implement `BaseProvider` in `src/experimentos/integrations/`
2. Register in `registry.py`
3. Add connection UI in `IntegrationConnect.tsx`
4. Add tests in `tests/test_integrations.py`

### Adding a New Guardrail Type
1. Extend `calculate_guardrails()` / `calculate_guardrails_multivariant()` in `analysis.py`
2. Update guardrail card rendering in `Dashboard.tsx`
3. Update decision rules if needed in `memo.py`

---

## 8. Deployment

### Frontend (Vercel)
```bash
cd experimentos-guardrails
vercel --prod
```

### Backend (Render)
GitHub main branch push triggers auto-deploy. See `render.yaml`.

### Docker (Local)
```bash
docker build -t experimentos-api .
docker run -p 8000:8000 experimentos-api
```

### Environment Variables
See `.env.example` for required configuration.

---

## 9. Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
**Fix**: Run from project root; ensure `PYTHONPATH` includes project directory.

**Issue**: TypeScript errors with multi-variant types
**Fix**: Ensure `noUncheckedIndexedAccess: true` in tsconfig.json. Use type guards before accessing variant-specific properties.

**Issue**: Bayesian tests flaky
**Fix**: Fix RNG seed and loosen assertions to robust thresholds.

**Issue**: Multi-variant guardrails show empty
**Fix**: Ensure CSV has guardrail columns (prefixed with `guardrail_` or matching guardrail names).
