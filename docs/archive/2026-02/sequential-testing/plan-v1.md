# ExperimentOS PDCA Plan v1.0

> A/B 테스트 의사결정 자동화 플랫폼 — 현황 분석 및 다음 단계 계획
> 작성일: 2026-02-10

---

## 1. 프로젝트 개요

### 1.1 한 줄 정의
실험(A/B) 결과 데이터를 입력하면 **SRM/효과크기(CI)/가드레일**을 자동 검증하고,
**Launch/Hold/Rollback 결정 메모(1-pager)**를 생성해 실험 의사결정의 속도와 일관성을 높이는 **Decision Layer** 플랫폼.

### 1.2 Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13+ / FastAPI 0.115+ / scipy / statsmodels / pandas |
| Frontend (Web) | React 19 / TypeScript 5.8 / Vite 6.4 / Tailwind CSS v4 / Recharts 3 |
| Frontend (Local) | Streamlit 1.29+ |
| Test | pytest 8+ (152 tests) |
| Deploy | Vercel (frontend) / Render (backend) |

### 1.3 타겟 사용자
| Persona | 역할 | 니즈 |
|---------|------|------|
| 데이터 분석가 | Primary | 검증/리포트/결정 메모 표준화로 리드타임 단축 |
| PM/PO | Decision Maker | 결론 + 근거 + 리스크 + 다음 액션을 한 장으로 파악 |
| 엔지니어 | Secondary | 롤아웃/롤백 판단 기준이 명확한 메모 수령 |

---

## 2. 현재 구현 상태 (As-Is)

### 2.1 완료된 기능 (Phase 1 - Quick Wins)

#### Core Pipeline
| 기능 | 상태 | 파일 |
|------|------|------|
| CSV 업로드 + 스키마 검증 | ✅ 완료 | `healthcheck.py`, `FileUpload.tsx` |
| SRM 자동 탐지 (N-variant) | ✅ 완료 | `healthcheck.py` |
| Primary 분석 (z-test) | ✅ 완료 | `analysis.py` |
| Guardrail 비교 | ✅ 완료 | `analysis.py` |
| Decision Memo 생성 | ✅ 완료 | `memo.py`, `DecisionMemo.tsx` |
| MD/HTML Export | ✅ 완료 | `memo.py` |

#### Multi-Variant 지원
| 기능 | 상태 | 파일 |
|------|------|------|
| Variant 자동 감지 | ✅ 완료 | `backend/main.py` (`_is_multivariant`) |
| Chi-square overall test | ✅ 완료 | `analysis.py` |
| Pairwise z-test + p-value 보정 | ✅ 완료 | `analysis.py` (Bonferroni/Holm/FDR_BH) |
| Multi-variant guardrails | ✅ 완료 | `analysis.py` |
| Multi-variant Bayesian | ✅ 완료 | `bayesian.py` |
| Multi-variant decision rules | ✅ 완료 | `memo.py` |
| Frontend 분기 (union types) | ✅ 완료 | `types.ts`, `Dashboard.tsx` |

#### 외부 플랫폼 연동
| Provider | 상태 | 파일 |
|----------|------|------|
| Statsig | ✅ 완료 | `integrations/statsig.py` |
| GrowthBook | ✅ 완료 | `integrations/growthbook.py` |
| Hackle | ✅ 완료 | `integrations/hackle.py` |
| Registry 패턴 | ✅ 완료 | `integrations/registry.py` |
| Cache/Retry | ✅ 완료 | `integrations/cache.py`, `retry.py` |

#### 시각화
| 기능 | 상태 | 파일 |
|------|------|------|
| Forest Plot | ✅ 완료 | `charts/ForestPlot.tsx` |
| Posterior Distribution | ✅ 완료 | `charts/PosteriorDistribution.tsx` |
| Power Curve | ✅ 완료 | `charts/PowerCurve.tsx` |
| Chart Theme/Utils | ✅ 완료 | `charts/chartTheme.ts`, `chartUtils.ts` |

#### UX 개선
| 기능 | 상태 | 파일 |
|------|------|------|
| Guided Tour | ✅ 완료 | `TourOverlay.tsx`, `hooks/useTour.ts` |
| Glossary Tooltips | ✅ 완료 | `GlossaryTerm.tsx`, `data/glossary.ts` |
| Demo Data | ✅ 완료 | `data/demoData.ts` |
| Power Calculator | ✅ 완료 | `PowerCalculator.tsx`, `power.py` |
| Experiment Charter | ✅ 완료 | `ExperimentMetadata.tsx` |

#### 연속형 지표
| 기능 | 상태 | 파일 |
|------|------|------|
| Welch's t-test | ✅ 완료 | `continuous_analysis.py` |
| Continuous UI | ✅ 완료 | `ContinuousMetrics.tsx` |

### 2.2 테스트 현황
- **총 152개 테스트** 전부 통과
- Decision regression 테스트 안정 (`test_decision.py`, `test_decision_branches.py`)
- Multi-variant 테스트 21개 추가
- Frontend: Vite 빌드 성공 (~850ms)

### 2.3 배포 현황
| 환경 | URL | 플랫폼 |
|------|-----|--------|
| Frontend | https://experimentos-guardrails.vercel.app | Vercel |
| Backend | https://experimentos-api.onrender.com | Render (Free Tier) |

---

## 3. Gap 분석 (PRD vs 구현 vs 로드맵)

### 3.1 PRD (MVP) 대비 초과 달성
PRD는 2-variant MVP만 정의했으나, 현재 구현은 이를 크게 초과:
- ✅ Multi-variant (N-variant) 전체 파이프라인
- ✅ 외부 플랫폼 연동 3개 (Statsig, GrowthBook, Hackle)
- ✅ 베이지안 분석 + 시각화
- ✅ 연속형 지표 (Welch's t-test)
- ✅ React 프론트엔드 (Vercel 배포)
- ✅ 인터랙티브 온보딩 투어
- ✅ 용어집 툴팁

### 3.2 로드맵 Phase 1 완료율: ~95%
| 로드맵 항목 | 상태 |
|------------|------|
| 1-1. API 연동 | ✅ 완료 |
| 1-2. Multi-Variant | ✅ 완료 |
| 1-3. 시각화 강화 | ✅ 완료 |
| 1-4. 인터랙티브 튜토리얼 | ✅ 완료 |

### 3.3 미구현 기능 (Phase 2 로드맵)
| 기능 | 우선순위 | 난이도 | 비고 |
|------|---------|--------|------|
| Sequential Testing (조기 종료) | CRITICAL | HIGH | O'Brien-Fleming boundary |
| Segmentation Analysis | HIGH | HIGH | 세그먼트별 HTE |
| 실험 히스토리 DB | HIGH | MEDIUM | PostgreSQL/DuckDB |
| 팀 협업 (댓글/승인) | MEDIUM-HIGH | HIGH | 인증 필요 |

### 3.4 기술 부채 (Technical Debt)
| 항목 | 현재 상태 | 개선 방향 |
|------|---------|----------|
| 데이터 저장 | session_state (Streamlit) / Stateless API | DB 도입 필요 |
| 인증/인가 | 없음 | JWT/OAuth2 필요 (팀 협업 시) |
| E2E 테스트 | 없음 | Playwright 도입 권장 |
| 에러 트래킹 | 없음 | Sentry 연동 권장 |
| Rate Limiting | 없음 | FastAPI middleware 추가 |
| Render 슬립 | 15분 비활성 시 슬립 | 유료 전환 또는 AWS 마이그레이션 |

---

## 4. 다음 단계 계획 (To-Be)

### 4.1 Phase 2A: 핵심 차별화 기능 (우선 구현)

#### Feature 1: Sequential Testing (조기 종료)
- **목표**: 실험 기간 30% 단축
- **범위**:
  - O'Brien-Fleming alpha spending function
  - Sequential confidence intervals
  - "지금 종료 가능" / "더 기다려야 함" 판정
  - Power calculator에 sequential 옵션 추가
- **구현 위치**:
  - `src/experimentos/sequential.py` (신규)
  - `backend/main.py` 엔드포인트 추가
  - `experimentos-guardrails/components/SequentialMonitor.tsx` (신규)
- **테스트**: boundary 계산 정확도, early stop 판정 regression
- **의존성**: 없음 (독립 구현 가능)

#### Feature 2: 실험 히스토리 DB
- **목표**: 실험 결과 영구 저장 및 조회
- **범위**:
  - DB 스키마 설계 (experiments, analysis_results, decision_memos)
  - CRUD API 엔드포인트
  - 실험 목록 페이지 (필터/검색/정렬)
  - 과거 분석 결과 조회
- **기술 선택**: DuckDB (경량, Python-native) 또는 PostgreSQL (확장성)
- **의존성**: 없음 (독립 구현 가능)

### 4.2 Phase 2B: 분석 고도화

#### Feature 3: Segmentation Analysis
- **목표**: 세그먼트별 이질적 효과(HTE) 탐지
- **범위**:
  - CSV `segment` 컬럼 지원
  - 세그먼트별 lift 계산 + interaction effect
  - 세그먼트 비교 시각화
- **의존성**: 히스토리 DB (결과 저장)

#### Feature 4: CUPED (Variance Reduction)
- **목표**: 실험 민감도 향상 (같은 샘플로 더 작은 효과 탐지)
- **범위**:
  - Pre-experiment 공변량 활용
  - CUPED-adjusted lift + CI 계산
- **의존성**: Segmentation (입력 스키마 공유)

### 4.3 Phase 2C: 인프라 개선

#### Infra 1: E2E 테스트 (Playwright)
- Frontend 핵심 플로우 자동 검증
- CSV 업로드 → 분석 → Decision Memo 다운로드

#### Infra 2: 에러 트래킹 (Sentry)
- Backend/Frontend 에러 자동 수집
- 성능 모니터링

#### Infra 3: Rate Limiting
- FastAPI middleware로 API 요청 제한
- 남용 방지

---

## 5. 구현 우선순위 매트릭스

```
                    높은 비즈니스 가치
                         │
    Sequential Testing ──┤── 실험 히스토리 DB
    (차별화 + 실무 필수)  │   (B2B 전환 필수)
                         │
    ─────────────────────┼───────────────────── 높은 구현 복잡도
                         │
    E2E Test + Sentry ───┤── Segmentation
    (품질 안정성)         │   (인사이트 깊이)
                         │
                    낮은 비즈니스 가치
```

### 권장 구현 순서
1. **Sequential Testing** — 핵심 차별화, 독립 구현 가능
2. **실험 히스토리 DB** — B2B 전환 필수, 후속 기능 기반
3. **E2E 테스트 + Sentry** — 품질 안정화 (병렬 진행 가능)
4. **Segmentation Analysis** — DB 기반 위에 구축

---

## 6. 리스크 및 완화 전략

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|------|------|----------|
| Render 슬립으로 첫 응답 30-60초 | 사용자 이탈 | 높음 | Cron ping 또는 유료 전환 |
| Sequential Testing 통계 오류 | 잘못된 조기 종료 결정 | 중간 | 학술 검증 + 광범위 테스트 |
| DB 도입 시 기존 API 호환성 | 기존 사용자 영향 | 낮음 | 하위 호환 유지 (stateless 모드 병존) |
| 테스트 부재로 프론트엔드 리그레션 | 기능 깨짐 | 중간 | E2E 테스트 우선 도입 |

---

## 7. 성공 지표 (KPIs)

### Phase 2 목표
| 지표 | 현재 | 목표 |
|------|------|------|
| 주간 활성 사용자 (WAU) | 측정 불가 | 100명 |
| 실험 분석 리드타임 | ~20분 (수동) | 5분 이하 |
| 테스트 커버리지 | 152 unit tests | +E2E 10 flows |
| API 연동 사용률 | 미측정 | 30% |
| Sequential Testing 사용률 | N/A | 20% (도입 후) |

---

## 8. 타임라인 (추정)

| 주차 | 작업 | 산출물 |
|------|------|--------|
| Week 1-2 | Sequential Testing 설계 + 구현 | `sequential.py` + API + 테스트 |
| Week 3-4 | Sequential Testing 프론트엔드 | `SequentialMonitor.tsx` + 통합 |
| Week 3-4 | 실험 히스토리 DB 스키마 설계 | DB migration + CRUD API |
| Week 5-6 | 히스토리 UI + E2E 테스트 셋업 | 실험 목록 페이지 + Playwright |
| Week 7-8 | Segmentation 백엔드 | 세그먼트 분석 로직 + API |
| Week 9-10 | Segmentation 프론트엔드 | 세그먼트 비교 UI |
| Week 11-12 | 통합 테스트 + 안정화 | 전체 regression 확인 |

---

## 9. PDCA 사이클 정의

| Phase | 활동 | 산출물 |
|-------|------|--------|
| **Plan** | 현황 분석, 기능 정의, 우선순위 설정 | 이 문서 (`plan-v1.md`) |
| **Design** | 기술 설계, API 스펙, DB 스키마, UI 와이어프레임 | `docs/02-design/` |
| **Do** | 구현 + 단위 테스트 + 코드 리뷰 | 소스 코드 + 테스트 |
| **Check** | Gap 분석 (설계 vs 구현), 코드 품질 점검 | `docs/03-analysis/` |
| **Act** | 개선 반복, 배포, 회고 | `docs/04-report/` |

---

*문서 버전: v1.0*
*최종 수정: 2026-02-10*
*작성: Claude Code (PDCA Plan)*
