# ExperimentOS - A/B Test Analysis Platform

프리미엄 디자인의 React + FastAPI 기반 A/B 테스트 분석 플랫폼입니다.

## 🎨 주요 기능

- **헬스 체크**: CSV 파일의 스키마 검증 및 SRM(Sample Ratio Mismatch) 검사
- **베이지안 분석**: Primary 메트릭과 Guardrail 메트릭에 대한 통계 분석
- **인터랙티브 대시보드**: 실시간 결과 시각화 및 메트릭 테이블
- **프리미엄 UI**: Dark mode glassmorphism 디자인

## 🏗️ 기술 스택

### Frontend
- **React 19** with TypeScript
- **Tailwind CSS v4** (CSS-first configuration)
- **Vite** for blazing fast builds
- **Axios** for API communication

### Backend
- **FastAPI** for high-performance API
- **Pandas** for data processing
- **SciPy/NumPy** for statistical analysis

## 📦 로컬 실행

### 1. Backend 실행
```bash
cd e:\프로젝트\안티그래비티 프로젝트\에이블리
python -m uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend 실행
```bash
cd experimentos-guardrails
npm install
npm run dev
```

브라우저에서 **http://localhost:3000** 접속

## 🚀 배포

자세한 배포 가이드는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참조하세요.

### Quick Deploy to Vercel (Frontend)
```bash
cd experimentos-guardrails
vercel
```

## 📁 프로젝트 구조

```
experimentos-guardrails/
├── api/
│   └── client.ts              # API client & TypeScript types
├── components/
│   ├── Dashboard.tsx          # Main dashboard
│   ├── FileUpload.tsx         # Drag-and-drop upload
│   ├── MetricsTable.tsx       # Analysis results table
│   ├── Sidebar.tsx            # Navigation
│   ├── StatsCard.tsx          # Metric cards
│   └── Icon.tsx               # Icon component
├── src/
│   └── vite-env.d.ts          # TypeScript env definitions
├── App.tsx                    # Main application
├── index.tsx                  # React entry point
├── index.css                  # Tailwind v4 theme
├── vercel.json                # Vercel deployment config
└── DEPLOYMENT.md              # Deployment guide

backend/
└── main.py                    # FastAPI application

src/experimentos/
├── analysis.py                # Statistical analysis logic
├── healthcheck.py             # Data validation logic
├── config.py                  # Configuration
└── state.py                   # State management
```

## 🎯 API Endpoints

### `POST /api/health-check`
CSV 파일의 스키마 검증 및 SRM 체크

**Request**: `multipart/form-data` with `file`
**Response**:
```json
{
  "status": "success",
  "result": {
    "overall_status": "Healthy",
    "schema": { "status": "valid", "issues": [] },
    "srm": null
  },
  "filename": "data.csv"
}
```

### `POST /api/analyze`
베이지안 분석 수행

**Request**: `multipart/form-data` with `file`
**Response**:
```json
{
  "status": "success",
  "primary_result": {
    "control": { "rate": 0.15 },
    "treatment": { "rate": 0.18 },
    "relative_lift": 0.20,
    "p_value": 0.001,
    "is_significant": true
  },
  "guardrail_results": [...]
}
```

## 🎨 디자인 시스템

- **Colors**: 
  - Primary: `#10b981` (Emerald)
  - Background: `#11211c` (Deep Dark)
  - Secondary: `#1a2c26`
- **Typography**: Inter (Display), JetBrains Mono (Code)
- **Effects**: Glassmorphism, Backdrop Blur, Smooth Animations

## 📝 환경 변수

### Frontend `.env.local`
```bash
VITE_API_URL=http://localhost:8000/api  # Development
# VITE_API_URL=https://your-backend.fly.io/api  # Production
```

## 🧪 테스트

빌드 검증:
```bash
npm run build
```

## 📄 라이선스

Private Project

## 🚧 개발 현황

- [x] React Frontend with Premium Design
- [x] FastAPI Backend Integration
- [x] File Upload & Health Check
- [x] Bayesian Analysis
- [x] Interactive Dashboard
- [x] TypeScript Type Safety
- [x] Build Optimization
- [ ] Backend Deployment (Fly.io/Railway)
- [ ] Production Vercel Deployment with Backend URL
