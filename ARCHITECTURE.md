# ExperimentOS Architecture

## 1. Tech Stack

### Core Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13+ | Core language (async support, modern type hints) |
| **Streamlit** | 1.29+ | UI framework (multi-page apps, session state, built-in widgets) |
| **pandas** | 2.2+ | Data manipulation (CSV handling, DataFrame operations) |
| **scipy** | 1.11+ | Statistical tests (chi-square for SRM, proportions test) |
| **statsmodels** | 0.14+ | Advanced statistics (confidence intervals, z-test) |
| **markdown** | 3.5+ | Markdown to HTML conversion for export |

### Why These Choices?
- **Streamlit**: Fastest path to MVP for data-centric apps. Built-in multi-page support eliminates routing complexity.
- **scipy + statsmodels**: Industry-standard for A/B testing statistics. Well-tested implementations of z-test, CI calculations.
- **Session State**: Zero database overhead for MVP. Enables instant iteration without persistence layer complexity.

### Assumed (Not Implemented in MVP)
- **SQLite/DuckDB**: For experiment history (V1 roadmap)
- **Docker**: For containerized deployment
- **pytest-cov**: For coverage reporting

---

## 2. Folder Structure

```
.
├── app.py                          # Streamlit entry point, page config, session init
├── pages/                          # Streamlit multi-page apps (auto-discovered)
│   ├── 1_Home.py                  # Session state summary, quick start guide
│   ├── 2_New_Experiment.py        # CSV upload, metadata input, Health Check UI
│   ├── 3_Results.py               # Primary/Guardrail analysis, Decision UI
│   └── 4_Decision_Memo.py         # Memo generation, MD/HTML export
├── src/experimentos/               # Business logic (stateless, testable)
│   ├── __init__.py
│   ├── state.py                   # Session state initialization & helpers
│   ├── logger.py                  # Centralized logging setup
│   ├── healthcheck.py             # Schema validation, SRM detection
│   ├── analysis.py                # Primary/Guardrail calculations
│   └── memo.py                    # Decision rules, memo generation, HTML export
├── tests/                          # Unit tests (pytest)
│   ├── __init__.py
│   ├── test_healthcheck.py        # SRM, schema validation tests
│   ├── test_analysis.py           # Primary calculation, CI tests
│   └── test_decision.py           # Decision framework tests
├── .tmp/                           # Sample CSV files, temp artifacts
├── requirements.txt                # Python dependencies (pinned versions)
└── README.md                       # User-facing docs, quickstart
```

### Folder Responsibilities
- **`pages/`**: UI layer only. Call `src/` functions, display results with Streamlit widgets.
- **`src/experimentos/`**: Pure functions. Input = DataFrame/dict, Output = dict. No Streamlit imports.
- **`tests/`**: Unit tests for `src/` modules. Use pytest, assert on return dictionaries.

---

## 3. Coding Conventions

### Formatting
- **Line length**: 100 characters max
- **Indentation**: 4 spaces (Python standard)
- **Imports**: Grouped (stdlib → third-party → local), sorted alphabetically

### Naming
- **Functions**: `snake_case` (e.g., `calculate_primary`, `detect_srm`)
- **Variables**: `snake_case` (e.g., `conversion_rate`, `p_value`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SPLIT`, `SEVERE_THRESHOLD`)
- **Classes**: `PascalCase` (not used in MVP)

### Type Hints
```python
from typing import Dict, List, Optional, Tuple

def calculate_primary(df: pd.DataFrame) -> Dict:
    """Returns dict with keys: control, treatment, absolute_lift, ..."""
    ...
```
- **All public functions** must have type hints
- Use `Dict`, `List` from `typing` (not `dict`, `list` for Python 3.9 compat)

### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.warning(f"Operation failed: {e}")
    return default_safe_value
```
- **Catch specific exceptions**, not bare `except:`
- **Log errors** with context (function name, input summary)
- **Return safe defaults** (e.g., `p_value=1.0` on calculation failure)

### Logging
```python
import logging
logger = logging.getLogger("experimentos")

logger.info("Processing CSV with 10000 rows")
logger.warning("SRM detected: p=0.0001")
logger.error(f"Calculation failed: {e}")
```
- Use module-level logger: `logger = logging.getLogger("experimentos")`
- Levels: `INFO` for normal flow, `WARNING` for recoverable issues, `ERROR` for failures

### Tests
```python
def test_calculate_primary_significant():
    """Primary analysis with significant difference (p < 0.05)"""
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "conversions": [1000, 1200]
    })
    
    result = calculate_primary(df)
    
    assert result["is_significant"] is True
    assert result["p_value"] < 0.05
    assert 0.01 < result["absolute_lift"] < 0.03  # 10% vs 12% = ~2%p
```
- **Test naming**: `test_<function>_<scenario>` (e.g., `test_srm_warning`)
- **Arrange-Act-Assert** pattern
- **Assert on dict keys** returned by functions

---

## 4. How to Add New Features

### Adding a New Metric (e.g., Revenue Per User)

**Step 1**: Update CSV schema (optional columns)
```csv
variant,users,conversions,revenue_total
control,10000,1200,50000
treatment,10000,1320,55000
```

**Step 2**: Add calculation function to `src/experimentos/analysis.py`
```python
def calculate_revenue_per_user(df: pd.DataFrame) -> Dict:
    """Calculate RPU (Revenue Per User)"""
    control_row = df[df["variant"] == "control"].iloc[0]
    treatment_row = df[df["variant"] == "treatment"].iloc[0]
    
    rpu_c = control_row["revenue_total"] / control_row["users"]
    rpu_t = treatment_row["revenue_total"] / treatment_row["users"]
    
    delta = rpu_t - rpu_c
    relative = (rpu_t / rpu_c) - 1 if rpu_c > 0 else 0.0
    
    return {
        "control_rpu": rpu_c,
        "treatment_rpu": rpu_t,
        "delta": delta,
        "relative_lift": relative
    }
```

**Step 3**: Add UI to `pages/3_Results.py`
```python
# In Results page, after Primary section
st.subheader("💰 Revenue Per User")

rpu_result = calculate_revenue_per_user(df)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Control RPU", f"${rpu_result['control_rpu']:.2f}")
with col2:
    st.metric("Treatment RPU", f"${rpu_result['treatment_rpu']:.2f}",
              delta=f"${rpu_result['delta']:.2f}")
with col3:
    st.metric("Relative Lift", f"{rpu_result['relative_lift']:+.1%}")
```

**Step 4**: Add unit test to `tests/test_analysis.py`
```python
def test_calculate_revenue_per_user():
    df = pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10000, 10000],
        "revenue_total": [50000, 55000]
    })
    
    result = calculate_revenue_per_user(df)
    
    assert result["control_rpu"] == 5.0
    assert result["treatment_rpu"] == 5.5
    assert abs(result["delta"] - 0.5) < 0.01
```

### Adding a New Page (e.g., History)

**Step 1**: Create `pages/5_History.py`
```python
"""
History 페이지

실험 히스토리 조회 (V1 feature)
"""

import streamlit as st
from src.experimentos.state import initialize_state

initialize_state()

st.title("📚 History")

st.info("실험 히스토리 기능은 V1에서 제공됩니다.")
# TODO: Add DB integration for experiment history
```

**Step 2**: (Optional) Add state management in `src/experimentos/state.py`
```python
def initialize_state():
    # ... existing initialization ...
    
    if "history" not in st.session_state:
        st.session_state.history = []  # List of past experiments
```

**Step 3**: Update README.md
```markdown
## Pages (Streamlit)

1. **Home**: 현재 세션 상태 요약
2. **New Experiment**: CSV 업로드 & Health Check
3. **Results**: Primary + Guardrail + Decision
4. **Decision Memo**: 1pager export
5. **History**: 실험 히스토리 (V1)
```

---

## 5. Decision Logic Module Boundaries

### Module Separation Principle
Each module has a **single responsibility** and **no side effects** (except logging).

```
CSV Upload (UI)
    ↓
healthcheck.py → {status: "Healthy/Warning/Blocked", issues: [...], srm: {...}}
    ↓
analysis.py → {primary: {...}, guardrails: [...]}
    ↓
memo.py (make_decision) → {decision: "Launch/Hold/Rollback", reason: "...", details: [...]}
    ↓
memo.py (generate_memo) → "# Decision Memo: ..."
    ↓
Decision Memo UI (Download MD/HTML)
```

### `healthcheck.py`
**Responsibility**: Data quality validation  
**Inputs**: `pd.DataFrame`, `expected_split: Tuple[float, float]`  
**Outputs**: `Dict` with keys: `schema`, `srm`, `overall_status`

**Functions**:
- `validate_schema(df)`: Check columns, types, logic (conversions ≤ users)
- `detect_srm(control_users, treatment_users)`: Chi-square test for traffic imbalance
- `run_health_check(df)`: Orchestrate schema + SRM checks

**Rules**:
- If schema `Blocked` → skip SRM check
- SRM thresholds: `p < 0.001` = Warning, `p < 0.00001` = Blocked

### `analysis.py`
**Responsibility**: Statistical calculations  
**Inputs**: `pd.DataFrame`  
**Outputs**: `Dict` with analysis results

**Functions**:
- `calculate_primary(df)`: Conversion rate, lift, CI, p-value (two-proportion z-test)
- `calculate_guardrails(df, guardrail_columns)`: Guardrail rates, delta, worsened/severe flags

**Rules**:
- Use `statsmodels.stats.proportion` for z-test and CI
- Guardrail thresholds: `worsened` if Δ > 0.1%p, `severe` if Δ > 0.3%p

### `memo.py`
**Responsibility**: Decision rules + memo generation  
**Inputs**: `health: Dict`, `primary: Dict`, `guardrails: List[Dict]`  
**Outputs**: `Dict` (decision) or `str` (markdown memo)

**Functions**:
- `make_decision(health, primary, guardrails)`: Apply 6-rule decision framework
- `generate_memo(...)`: Create 1-pager markdown
- `export_html(markdown_content)`: Convert MD → HTML with CSS

**Decision Rules** (evaluated in order):
1. `health["overall_status"] == "Blocked"` → **Hold**
2. `health["srm"]["status"] in ["Warning", "Blocked"]` → **Hold**
3. `primary["is_significant"] and severe_guardrails` → **Rollback**
4. `primary["is_significant"] and worsened_guardrails` → **Hold**
5. `primary["is_significant"] and no worsened` → **Launch**
6. `not primary["is_significant"]` → **Hold**

### `state.py`
**Responsibility**: Streamlit session state management  
**Inputs**: None (uses `st.session_state`)  
**Outputs**: None (mutates session state)

**Functions**:
- `initialize_state()`: Set default values for all session keys
- `reset_state()`: Clear all state, re-initialize
- `has_data()`, `has_health_check()`: Convenience checkers

**Session Keys**:
- `data`: `pd.DataFrame` (uploaded CSV)
- `experiment_name`: `str`
- `expected_split`: `Tuple[float, float]`
- `health_result`: `Dict` (from `healthcheck.py`)
- `primary_result`: `Dict` (from `analysis.py`)
- `guardrails`: `List[Dict]` (from `analysis.py`)
- `decision`: `Dict` (from `memo.py`)
- `memo_markdown`: `str` (generated memo)

---

## 6. Testing Strategy

### Unit Test Coverage
- **`test_healthcheck.py`**: SRM detection (healthy/warning/blocked), schema validation (missing columns, conversions > users, zero users)
- **`test_analysis.py`**: Primary calculation (significant/not significant, zero conversions, negative lift)
- **`test_decision.py`**: All 6 decision rules (blocked, SRM, severe, worsened, launch, hold)

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_decision.py -v

# Run with coverage (future)
pytest tests/ --cov=src/experimentos --cov-report=html
```

### Manual UX Tests (Pre-Release Checklist)
- [ ] Upload without data → friendly warning message
- [ ] Upload `sample_launch.csv` → Launch decision
- [ ] Upload `sample_srm_warning.csv` → Hold decision (SRM)
- [ ] Upload `sample_guardrail_worsened.csv` → Hold/Rollback decision
- [ ] Download MD memo → valid Markdown file
- [ ] Download HTML memo → renders correctly in browser

---

## 7. Extension Points (V1 Roadmap)

### Experiment History (Database Integration)
- Add `src/experimentos/db.py` with SQLite/DuckDB connection
- Schema: `experiments` table (id, name, date, decision, memo_md)
- Update `pages/1_Home.py` to show past experiments
- Add `pages/5_History.py` for detailed history view

### Segment Breakdown (Cohort Analysis)
- Extend CSV schema: `segment` column (e.g., "new", "returning", "heavy")
- Add `calculate_segment_primary(df, segment_name)` to `analysis.py`
- Add `pages/6_Segments.py` with segment comparison table

### CUPED (Variance Reduction)
- Require pre-experiment metric in CSV: `pre_conversion_rate`
- Add `calculate_cuped(df, covariate_col)` to `analysis.py`
- Adjust CI calculations with reduced variance

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
# .env (optional, not required for MVP)
LOG_LEVEL=INFO
SRM_WARNING_THRESHOLD=0.001
SRM_BLOCKED_THRESHOLD=0.00001
GUARDRAIL_WORSENED_THRESHOLD=0.001
GUARDRAIL_SEVERE_THRESHOLD=0.003
```

### Security Notes
- **Do not commit** `.env` or real experiment data
- Use `.gitignore` for `*.csv`, `*.env`, `__pycache__/`
- Sanitize inputs: `pd.to_numeric(..., errors='raise')` prevents injection

---

## 9. Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`  
**Fix**: Run from project root, ensure `PYTHONPATH` includes project directory

**Issue**: Streamlit doesn't refresh after code changes  
**Fix**: Click "Rerun" button or enable "Always rerun" in settings

**Issue**: `KeyError` in session state  
**Fix**: Call `initialize_state()` at top of every page

**Issue**: SRM p-value = 1.0 (wrong)  
**Fix**: Check `scipy.stats.chisquare` input order (`f_obs`, `f_exp`)

---

## Contributing

When adding new features:
1. **Plan**: Update `ARCHITECTURE.md` if adding new modules
2. **Implement**: Follow coding conventions (Section 3)
3. **Test**: Add unit tests (Section 6)
4. **Document**: Update README.md and inline docstrings
5. **Review**: Run `pytest` and manual UX tests

---

**Last Updated**: 2026-02-02  
**Version**: MVP (5 PRs complete)
