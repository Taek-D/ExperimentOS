# ExperimentOS - Development Workflow

> A/B 테스트 의사결정 플랫폼. 헬스체크, 통계 분석, 의사결정 메모 자동 생성.

## Tech Stack

- **Backend**: Python 3.13+ / FastAPI / scipy / statsmodels / pandas
- **Frontend**: React 19 / TypeScript 5.8 / Vite / Tailwind CSS v4
- **Local UI**: Streamlit 1.29+
- **Test**: pytest 8+
- **Deploy**: Vercel (frontend) / Render (backend)

## Package Manager

- **Python**: `pip` (requirements.txt)
- **Frontend**: `npm` (experimentos-guardrails/package.json)

## Development Commands

### Backend (Python)

```bash
# Run FastAPI dev server
uvicorn backend.main:app --reload

# Run Streamlit local UI
streamlit run app.py

# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_analysis.py -v

# Lint
pylint src/ backend/

# Type check
mypy src/ backend/

# Format
black src/ backend/ tests/ --line-length 100
```

### Frontend (React)

```bash
cd experimentos-guardrails

# Dev server (port 3000)
npm run dev

# Build
npm run build

# Lint
npm run lint
```

## Project Structure

```
.
├── backend/                    # FastAPI API server
│   ├── main.py                 # Entry point, CORS, routers
│   ├── utils.py                # Utility functions
│   └── routers/                # API route modules
│       └── integrations.py     # Integration endpoints
│
├── src/experimentos/           # Business logic (stateless & testable)
│   ├── config.py               # Thresholds & tolerances (single source of truth)
│   ├── healthcheck.py          # Schema validation, SRM detection
│   ├── analysis.py             # Conversion + guardrail analysis orchestrator
│   ├── bayesian.py             # Beta-Binomial / posterior simulations
│   ├── continuous_analysis.py  # Welch t-test from sufficient statistics
│   ├── memo.py                 # Decision rules + memo generation
│   ├── power.py                # Sample size / power calculator
│   ├── state.py                # Streamlit session state helpers
│   ├── logger.py               # Logging setup
│   └── integrations/           # External platform integrations
│       ├── base.py             # Base provider interface
│       ├── statsig.py          # Statsig provider
│       ├── growthbook.py       # GrowthBook provider
│       ├── hackle.py           # Hackle provider
│       ├── dummy.py            # Dummy provider (testing)
│       ├── cache.py            # Cache layer
│       ├── retry.py            # Retry logic
│       ├── registry.py         # Provider registry
│       ├── schema.py           # Integration schemas
│       └── transform.py        # Data transformation
│
├── pages/                      # Streamlit multi-page UI
│   ├── 1_Home.py
│   ├── 2_New_Experiment.py
│   ├── 3_Results.py
│   └── 4_Decision_Memo.py
│
├── experimentos-guardrails/    # React frontend (Vercel)
│   ├── App.tsx                 # Main app & routing
│   ├── index.tsx               # Entry point
│   ├── types.ts                # TypeScript type definitions
│   ├── constants.ts            # Shared constants
│   ├── api/client.ts           # Axios API client
│   ├── components/             # React components
│   │   ├── BayesianInsights.tsx
│   │   ├── ContinuousMetrics.tsx
│   │   ├── Dashboard.tsx
│   │   ├── DecisionMemo.tsx
│   │   ├── ExperimentMetadata.tsx
│   │   ├── ExperimentSelector.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Icon.tsx
│   │   ├── IntegrationConnect.tsx
│   │   ├── MetricsTable.tsx
│   │   ├── PowerCalculator.tsx
│   │   ├── Sidebar.tsx
│   │   └── StatsCard.tsx
│   ├── vite.config.ts          # Vite config
│   ├── tsconfig.json           # TypeScript config
│   └── eslint.config.js        # ESLint config
│
├── tests/                      # pytest unit tests (20+ test files)
├── .claude/                    # Claude Code configuration
│   ├── commands/               # Custom slash commands
│   ├── agents/                 # Agent definitions
│   └── skills/                 # Skill definitions
│
├── app.py                      # Streamlit entry point
├── requirements.txt            # Python dependencies
├── constraints.txt             # Pip constraints
├── Dockerfile                  # Docker build config
├── render.yaml                 # Render deployment config
├── .env.example                # Environment variables template
└── ARCHITECTURE.md             # Architecture reference
```

## Coding Conventions

### Python

- **Line length**: 100 chars max
- **Indentation**: 4 spaces
- **Naming**: `snake_case` (functions/variables), `UPPER_SNAKE_CASE` (constants), `PascalCase` (classes)
- **Type hints**: 필수. built-in generics 사용 (`dict[str, ...]`, `list[...]` - `typing.Dict` 사용 금지)
- **Imports**: stdlib -> third-party -> local, 알파벳 순
- **Return values**: JSON-serializable 유지 (dict/list/str/float/bool)
- **Error handling**: 예외 대신 structured status 반환 (`Healthy/Warning/Blocked`)
- **Tolerances**: `config.py`에서 관리 (매직 넘버 금지)
- **RNG**: `numpy.random.default_rng(seed)` 사용, 테스트에서 seed 고정

### TypeScript/React

- **Strict mode** 활성화
- **Path alias**: `@/*` -> `./`
- React Hooks 규칙 준수
- Tailwind CSS v4 유틸리티 클래스 사용

## Architecture Rules

- `src/experimentos/`: 도메인 로직. pure functions 선호 (Streamlit import 최소화)
- `pages/`: UI layer only. session_state 읽기/쓰기, `src/experimentos/*` 호출
- `backend/`: FastAPI API layer. `src/experimentos/*` 호출
- **Decision은 frequentist/guardrail 기반**: `make_decision()`은 healthcheck + frequentist primary + guardrails만 사용
- **Bayesian 결과는 설명용**: 의사결정 로직에 영향 없음

## Testing Rules

- 새 기능은 반드시 기존 decision regression 테스트를 깨뜨리지 않아야 함
- Bayesian 테스트: RNG seed 고정, threshold assertion 선호 (tight assertion 금지)
- 테스트 실행 후 전체 통과 확인: `python -m pytest tests/ -v`

## Deployment

- **Frontend**: Vercel (`experimentos-guardrails/` 디렉토리)
- **Backend**: Render (`backend/main.py` -> `uvicorn backend.main:app`)
- 환경변수: `.env.example` 참조

## Do NOT

- `any` 타입 사용 (TypeScript)
- 매직 넘버 사용 (config.py에 정의)
- Bayesian 결과로 의사결정 로직 변경
- 기존 decision 테스트 깨뜨리기
- `typing.Dict/List/Tuple` 사용 (built-in generics 사용)
