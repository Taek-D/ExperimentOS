# ExperimentOS Architecture

> This document is the **single source of truth** for ExperimentOS structure, conventions, and extension points.  
> Last updated: 2026-02-02

## 1. Tech Stack

### Core Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13+ | Core language (modern type hints, stdlib improvements) |
| **Streamlit** | 1.29+ | UI framework (multi-page apps, session state, widgets) |
| **pandas** | 2.2+ | Data manipulation (CSV handling, DataFrame operations) |
| **numpy** | 2.0+ | Numeric primitives (vectorized math, RNG for simulation) |
| **scipy** | 1.11+ | Statistical tests (e.g., chi-square for SRM) |
| **statsmodels** | 0.14+ | Statistical models (two-proportion z-test, confidence intervals, power calcs) |
| **markdown** | 3.5+ | Markdown → HTML conversion for export |
| **pytest** | 8+ | Unit tests (`pytest -v`) |

### Why These Choices?
- **Streamlit**: fastest path to a usable MVP for data-centric apps; multi-page support avoids custom routing.
- **scipy + statsmodels**: battle-tested A/B building blocks (SRM, z-test, CIs, power).
- **numpy RNG**: deterministic Bayesian simulations in tests via fixed seeds.

---

## 2. Folder Structure

```
.
├── app.py                          # Streamlit entry point, page config, session init
├── pages/                          # Streamlit multi-page apps (auto-discovered)
│   ├── 1_Home.py                   # Session state summary, quick start guide
│   ├── 2_New_Experiment.py         # CSV upload, metadata input, Health Check UI (+ Charter/Power in PR2)
│   ├── 3_Results.py                # Primary/Guardrail analysis (+ Continuous/Bayesian tabs in PR1)
│   └── 4_Decision_Memo.py          # Memo generation, MD/HTML export (+ Charter/Bayes summary)
├── src/experimentos/               # Business logic (stateless & testable; minimal Streamlit imports)
│   ├── __init__.py
│   ├── config.py                   # Centralized thresholds & numeric tolerances (single source of truth)
│   ├── state.py                    # Session state initialization & helpers
│   ├── logger.py                   # Centralized logging setup
│   ├── healthcheck.py              # Schema validation, SRM detection, data-quality status
│   ├── analysis.py                 # Orchestrator: conversion + guardrails (+ continuous/bayes hooks)
│   ├── memo.py                     # Decision rules + memo generation + export
│   ├── continuous_analysis.py      # (PR1) Welch t-test from sufficient statistics
│   ├── bayesian.py                 # (PR1) Beta-Binomial + continuous posterior simulations
│   └── power.py                    # (PR2) Sample size / power calculator utilities
├── tests/                          # Unit tests (pytest)
├── .tmp/                           # Sample CSV files, temp artifacts
├── requirements.txt                # Python dependencies (pinned versions)
└── README.md                       # User-facing docs, quickstart
```

### Folder Responsibilities
- **`pages/`**: UI layer only. Read/write `st.session_state`, call `src/experimentos/*`, render widgets/tables.
- **`src/experimentos/`**: domain logic. Prefer *pure functions* with explicit inputs/outputs.  
  Exception: `state.py` (session helpers) and `logger.py` (logging setup).
- **`tests/`**: unit tests + small integration smoke (e.g., decision-regression invariants).

---

### CSV Schema Contracts (Required / Optional)

ExperimentOS uses **aggregated, 2-variant** experiment summaries. The app expects exactly **one control + one treatment** row per dataset.

#### Required columns (always)
- `variant`: `"control"` or `"treatment"`
- `users`: unique users exposed to the variant (non-negative int)
- `conversions`: number of users who converted (0 ≤ conversions ≤ users)

#### Optional continuous metric columns (sufficient statistics)
Continuous metrics must be provided as **sufficient statistics** per variant:
- `metric_sum`: \(\sum x_i\)
- `metric_sum_sq`: \(\sum x_i^2\)
- `n`: number of observations used for the metric mean

Supported column sets (examples):
- **Per-user revenue / ARPU / Revenue-per-user style**
  - `revenue_sum`, `revenue_sum_sq`
  - `n = users` (default)
- **AOV (per-order)**
  - `orders` (used as `n` when AOV mode is selected)
  - `aov_sum`, `aov_sum_sq`

> Notes:
> - `sum_sq` is required to estimate variance from aggregates:
>   \( s^2 = (\sum x_i^2 - (\sum x_i)^2 / n) / (n-1) \).
> - Negative sums can be valid (refunds), but `sum_sq` constraints must still hold.

#### Healthcheck validation rules (schema + logic)
- Basic:
  - `variant` must contain both `control` and `treatment`
  - `users > 0` (or explicitly handle `users=0` as Blocked)
  - `0 ≤ conversions ≤ users`
- Continuous (when any continuous column set is present):
  - **Completeness**: if a continuous column exists for one variant, it must exist for the other (**otherwise Blocked**)
  - **n validity**: `n >= 2` (needed for variance estimate); for per-user metrics use `users`, for AOV use `orders`
  - **Second moment constraint**: `sum_sq >= (sum^2)/n - tolerance`  
    where `tolerance` is configured in `config.py` to allow floating-point noise.
  - **Degenerate variance**: if implied variance ≤ 0 after tolerance handling → `Warning` or `Blocked` (policy in `healthcheck.py`)

---

### UI Conventions (Streamlit Pages)

**Global rule**: Every page must call `initialize_state()` at the top.

1) **Navigation guards**
- If the user hasn’t uploaded valid data, `Results` and `Decision Memo` pages must **not** proceed.
- Show a friendly `st.info(...)` with a CTA link to `New Experiment`.

2) **Status banners**
- `Healthy / Warning / Blocked` status must be rendered in a consistent “top banner” pattern.
- Blocked state should include **actionable reasons** (bullet list).

3) **Conditional tabs**
- If data for a tab isn’t available (e.g., no continuous columns), show an explanation instead of an empty chart/table.

---

## 3. Coding Conventions

### Formatting
- **Line length**: 100 characters max
- **Indentation**: 4 spaces
- **Imports**: stdlib → third-party → local; sorted alphabetically

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
- For numerical issues (division by zero, invalid variance), prefer:
  - **Blocked** when the input is inconsistent or unusable
  - **Warning** when usable but potentially misleading

### Numerical Stability & Randomness
- Use tolerances from `config.py` (no magic numbers scattered in modules).
- Clamp near-zero negative values caused by floating-point noise (document the rule in code).
- Bayesian simulations must:
  - use `numpy.random.default_rng(seed)`
  - default `seed` comes from config; tests should fix `seed` to avoid flakes.

---

## 4. How to Add New Features

### 4.1 Adding a New Continuous Metric (Aggregated Sufficient Stats)

**Step 1**: Extend CSV schema (add `*_sum`, `*_sum_sq`, and choose `n`)
```csv
variant,users,conversions,revenue_sum,revenue_sum_sq
control,10000,1200,50000,300000000
treatment,10000,1320,55000,360000000
```

**Step 2**: Implement metric math in `src/experimentos/continuous_analysis.py`
- Add/extend `analyze_continuous_from_sufficient_stats(...)` (Welch t-test + CI + lift).
- Handle edge cases:
  - `n < 2`
  - implied variance ≤ 0
  - `sum_sq < sum^2/n` beyond tolerance

**Step 3**: Wire it in `src/experimentos/analysis.py` (orchestrator)
- Keep conversion analysis unchanged.
- If continuous columns are present and healthcheck passes, compute continuous results and attach to the `results` dict.

**Step 4**: UI (`pages/3_Results.py`)
- Add a **Continuous Analysis** tab that is displayed only when continuous data exists.
- Follow navigation guards + status banner conventions.

**Step 5**: Tests
- Add `tests/test_continuous_analysis.py` (Welch calc + edge cases).
- Add healthcheck tests for continuous schema constraints.

---

### 4.2 Adding Bayesian View (Informational Only)

**Goal**: Provide interpretability without changing the decision rules.

- Implement Bayesian utilities in `src/experimentos/bayesian.py`.
- Render in `pages/3_Results.py` under a **Bayesian View** tab.
- Add to memo as **two summary lines** only.

**Hard rule**: Bayesian outputs must never affect `make_decision()` inputs or branching.

---

### 4.3 Adding Experiment Charter + Power Calculator (Pre-registration)

**Step 1**: Store charter in `st.session_state` via `src/experimentos/state.py`
- Provide `get_charter()` / `set_charter(...)` helpers.

**Step 2**: Implement sample size calculations in `src/experimentos/power.py`
- Conversion: `statsmodels` NormalIndPower + `proportion_effectsize`, ratio aware.
- Continuous: `TTestIndPower`, effect size = mde / std_dev (std_dev must be provided in UI).

**Step 3**: UI (`pages/2_New_Experiment.py`)
- Always show Charter inputs (fallback to N/A if empty).
- Show Power Calculator results: required n per group, total n, expected days.

**Step 4**: Memo integration
- `memo.py` adds a “Pre-registered Charter” section, but decision logic remains unchanged.

---

## 5. Decision Logic Module Boundaries

### Separation Principle
Each module has a single responsibility and minimal side effects (logging only).

```
CSV Upload (UI)
    ↓
healthcheck.py
    → {overall_status: Healthy/Warning/Blocked, issues: [...], srm: {...}}
    ↓
analysis.py (orchestrator)
    → {conversion_primary: {...}, guardrails: [...], continuous: {...}?, bayesian: {...}?}
    ↓
memo.py
    make_decision(health, primary, guardrails)  # Decision rule engine (unchanged)
    generate_memo(..., optional_bayes_summary, optional_charter)
    ↓
Decision Memo UI (Download MD/HTML)
```

### Core rule: Decision is frequentist/guardrail-driven
- `make_decision()` uses **healthcheck + frequentist primary + guardrails** only.
- Bayesian outputs are **explanatory**:
  - displayed in Results (Bayesian View tab)
  - summarized in Memo (2 lines)
  - never used to switch Launch/Hold/Rollback

### Planned/Extended Modules
- `continuous_analysis.py` (PR1): sufficient-stats continuous tests (Welch t-test).
- `bayesian.py` (PR1): Beta-Binomial and continuous posterior simulation.
- `power.py` (PR2): sample size/power computations for chartering.

---

## 6. Testing Strategy

### Test Layers
1) **Decision regression (must not change)**
- Existing PRD acceptance tests and `test_decision.py` must remain stable.
- Any new feature must not alter decision branching.

2) **Unit tests for new math modules**
- `test_continuous_analysis.py`: Welch + CI + edge cases
- `test_bayesian.py`: smoke + deterministic seed checks
- `test_power.py`: monotonicity (effect ↑ ⇒ required_n ↓), ratio smoke

3) **Healthcheck schema tests**
- Missing columns, partial variant completeness, continuous constraints (`sum_sq` and `n`) mapped to Warning/Blocked.

### Determinism Rules (for Bayesian tests)
- Fix RNG seed in config and in tests.
- Avoid assertions that are too tight; prefer monotonic or threshold assertions.

### Running Tests
```bash
python -m pytest tests/ -v
```

### Manual UX Smoke (Pre-Release Checklist)
- [ ] No data → Results/Memo show CTA to upload page
- [ ] Status banner is visible at top and includes actionable reasons
- [ ] Continuous/Bayesian tabs are conditional and do not render empty tables
- [ ] Memo export (MD/HTML) includes Bayes summary / Charter when available

---

## 7. Extension Points (V1 Roadmap)

### Experiment History (Database Integration)
- Add `src/experimentos/db.py` with SQLite/DuckDB connection
- Schema: `experiments` table (id, name, date, decision, memo_md)
- Update `pages/1_Home.py` to show past experiments
- Add `pages/5_History.py` for detailed view and re-run analysis

### Notion/Confluence Export (Optional)
- Add `export_notion()` / `export_confluence()` adapters in `memo.py` or `exports/` package.

---

## 8. Deployment Considerations

### Running in Production
```bash
# Local
streamlit run app.py

# Docker (future)
docker build -t experimentos .
docker run -p 8501:8501 experimentos

# Streamlit Cloud
# Push to GitHub, connect repo in Streamlit Cloud dashboard
```

### Environment Variables
```bash
# Optional: set log level
export EXPERIMENTOS_LOG_LEVEL=INFO
```

---

## 9. Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`  
**Fix**: Run from project root; ensure `PYTHONPATH` includes project directory.

**Issue**: Streamlit doesn't refresh after code changes  
**Fix**: Click "Rerun" or enable "Always rerun" in settings.

**Issue**: Continuous metric flagged as Blocked due to `sum_sq` constraint  
**Fix**: Ensure `*_sum_sq` represents \(\sum x^2\) at the observation level and matches `n` (users/orders).  
Check tolerance in `config.py` and confirm data aggregation pipeline.

**Issue**: Bayesian tests flaky  
**Fix**: Fix RNG seed and loosen assertions to robust thresholds.
