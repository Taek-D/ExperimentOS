---
name: experimentos-frontend
description: React 프론트엔드 구조, 컴포넌트, 스타일링. Use when working with React, TypeScript, Vite, Tailwind, components, frontend.
---

# Frontend Skill

## 기술 스택

- **React 19** + **TypeScript 5.8** (strict mode)
- **Vite 6.2** (빌드 도구)
- **Tailwind CSS v4** (스타일링)
- **Axios** (HTTP 클라이언트)

## 구조

```
experimentos-guardrails/
├── App.tsx                    # 메인 앱, 라우팅, 전역 상태
├── index.tsx                  # ReactDOM entry point
├── types.ts                   # 공유 TypeScript 타입 정의
├── constants.ts               # 공유 상수
├── api/
│   └── client.ts              # Axios API 클라이언트
├── components/
│   ├── Dashboard.tsx          # 분석 결과 대시보드
│   ├── DecisionMemo.tsx       # 의사결정 메모 표시/다운로드
│   ├── PowerCalculator.tsx    # 검정력/표본 크기 계산기
│   ├── ExperimentSelector.tsx # 연동 실험 목록에서 선택
│   ├── IntegrationConnect.tsx # 외부 플랫폼 API 키 연결
│   ├── FileUpload.tsx         # CSV 파일 드래그앤드롭 업로드
│   ├── BayesianInsights.tsx   # Bayesian 분석 결과 (설명용)
│   ├── ContinuousMetrics.tsx  # 연속 메트릭 t-test 결과
│   ├── ExperimentMetadata.tsx # 실험명, 트래픽 분배 입력
│   ├── MetricsTable.tsx       # Primary/Guardrail 메트릭 테이블
│   ├── Sidebar.tsx            # 사이드바 네비게이션
│   ├── StatsCard.tsx          # 통계 요약 카드
│   └── Icon.tsx               # Material Symbols 아이콘
├── vite.config.ts
├── tsconfig.json              # strict: true
├── eslint.config.js
├── postcss.config.js
└── package.json
```

## 상태 관리

**React useState + prop drilling** (별도 상태 관리 라이브러리 없음)

핵심 상태는 `App.tsx`에서 관리하고 하위 컴포넌트에 props로 전달:

| 상태 | 위치 | 설명 |
|------|------|------|
| `analysisResult` | App.tsx | 전체 분석 결과 (primary + guardrails) |
| `healthResult` | App.tsx | 헬스체크 결과 |
| `experimentName` | App.tsx | 현재 실험명 |
| `currentPage` | App.tsx | 현재 페이지 (dashboard, power 등) |
| `isConnected` | App.tsx | 외부 연동 연결 상태 |

**localStorage 사용** (IntegrationConnect):
- `integration_api_key`: 연동 API 키
- `integration_provider`: 연동 제공자 (statsig, growthbook, hackle)

## 데이터 흐름

```
FileUpload/IntegrationConnect
  -> POST /api/health-check (CSV 파일)
  -> POST /api/analyze (CSV 파일)
  -> POST /api/continuous-metrics
  -> POST /api/bayesian-analysis
  -> POST /api/decision-memo (JSON)
  -> Dashboard 렌더링
```

## Path Alias

- `@/*` -> `./` (tsconfig + vite 설정)

## API Client

- `api/client.ts`: Axios 인스턴스
- Base URL: `VITE_API_URL` (dev: localhost:8000, prod: Render)
- 모든 API 호출은 FormData (CSV) 또는 JSON

## 코딩 컨벤션

- **strict TypeScript**: `any` 금지, `noUncheckedIndexedAccess: true`
- **Tailwind CSS**: inline style 대신 유틸리티 클래스
- **React Hooks**: 규칙 준수 (react-hooks/rules-of-hooks)
- **컴포넌트**: functional component only
- 배열 인덱스 접근 시 반드시 undefined 체크 필요 (`noUncheckedIndexedAccess`)

## 개발 명령어

```bash
cd experimentos-guardrails
npm run dev       # 개발 서버 (port 3000)
npm run build     # 프로덕션 빌드
npm run preview   # 빌드 결과 미리보기
npm run lint      # ESLint 실행
npx tsc --noEmit  # 타입 체크
```

## 배포

- **Platform**: Vercel
- **Directory**: `experimentos-guardrails/`
- **Build**: `npm run build`
- **Output**: `dist/`
