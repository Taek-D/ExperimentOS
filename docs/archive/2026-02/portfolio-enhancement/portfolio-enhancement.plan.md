# Portfolio Enhancement Planning Document

> **Summary**: 데이터 분석가 포트폴리오로 포지셔닝 강화 — 노트북 중심 리프레이밍 + 분석 역량 보강
>
> **Project**: ExperimentOS
> **Author**: User
> **Date**: 2026-02-11
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

ExperimentOS를 **프로덕트/그로스 분석가** 포트폴리오로 최적화한다.
현재 프로젝트는 엔지니어링 비중이 높아 "도구를 만든 사람"으로 보이는데,
**"분석을 하고 의사결정까지 연결하는 사람"**으로 리프레이밍한다.

### 1.2 Background

현재 상태 분석:

| 강점 | 약점 |
|------|------|
| A/B 테스트 도메인 (면접 핵심) | 엔지니어링 70%, 분석 30% 비중 |
| 588K 실데이터 케이스 스터디 | EDA/시각화 기반 인사이트 부족 |
| SQL 9개 패턴 시연 | BI 도구(Tableau/Looker) 경험 미노출 |
| 통계 깊이 (SRM, Sequential, Bayesian) | 코호트/퍼널/리텐션 분석 부재 |
| 비즈니스 임팩트 $217K 산출 | 포트폴리오 전용 랜딩 페이지 없음 |

### 1.3 Related Documents

- [README.md](../../README.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Design Rationale](../design-rationale.md)

---

## 2. Scope

### 2.1 In Scope

- [ ] **FR-01**: 코호트/리텐션 분석 노트북 추가
- [ ] **FR-02**: 퍼널 분석 노트북 추가
- [ ] **FR-03**: README 리프레이밍 (분석가 관점)
- [ ] **FR-04**: 포트폴리오 요약 페이지 (GitHub Pages or Notion)

### 2.2 Out of Scope

- Tableau/Looker 대시보드 (별도 프로젝트로 분리)
- 새로운 백엔드/프론트엔드 기능 추가
- 기존 코드 리팩토링

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 코호트 리텐션 분석 노트북 — 마케팅 데이터 기반 Day-N 리텐션 곡선, 코호트별 전환율 히트맵 | High | Pending |
| FR-02 | 퍼널 분석 노트북 — 유저 여정(노출→클릭→전환) 단계별 이탈률, 세그먼트별 퍼널 비교 | High | Pending |
| FR-03 | README 리프레이밍 — "플랫폼 소개" → "분석 역량 쇼케이스" 구조로 변경. 노트북을 전면 배치, 엔지니어링은 부록 | Medium | Pending |
| FR-04 | 포트폴리오 요약 페이지 — 프로젝트별 한 줄 요약 + 핵심 발견 + 사용 기술 + 노트북 링크 (Notion 또는 GitHub Pages) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 재현성 | 모든 노트북 nbconvert 실행 에러 0 | `jupyter nbconvert --execute` |
| 스토리텔링 | 각 노트북 "문제 → 분석 → 발견 → 비즈니스 액션" 구조 | 리뷰 체크 |
| 시각화 | 노트북당 최소 3개 고품질 시각화 (matplotlib/seaborn) | 시각 확인 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 코호트 리텐션 노트북 작성 + nbconvert 실행 검증
- [ ] 퍼널 분석 노트북 작성 + nbconvert 실행 검증
- [ ] README 리프레이밍 완료
- [ ] 포트폴리오 요약 페이지 생성

### 4.2 Quality Criteria

- [ ] 모든 노트북 nbconvert 에러 0
- [ ] 각 노트북 시각화 3개 이상
- [ ] 비즈니스 임팩트 수치 포함 (매출, 전환율, ROI 등)
- [ ] 기존 209 tests 깨뜨리지 않음

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 마케팅 데이터에 코호트/리텐션 컬럼 부족 | High | Medium | 기존 588K 데이터에서 파생 가능한 지표로 대체, 또는 별도 공개 데이터셋 사용 |
| 노트북 추가가 프로젝트 범위를 벗어남 | Low | Low | notebooks/ 디렉토리에 격리, 기존 코드에 영향 없음 |
| README 변경으로 기존 사용자 혼란 | Medium | Low | 엔지니어링 정보를 삭제하지 않고 구조만 재배치 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Selected |
|-------|-----------------|:--------:|
| **Dynamic** | Feature-based modules, BaaS integration | ✅ |

기존 프로젝트 레벨 유지. 노트북 추가는 아키텍처에 영향 없음.

### 6.2 Key Decisions

| Decision | Selected | Rationale |
|----------|----------|-----------|
| 노트북 데이터 | 기존 Kaggle 588K + 파생 지표 | 일관된 데이터셋으로 스토리 연결 |
| 시각화 라이브러리 | matplotlib + seaborn | DA 업계 표준, 면접에서 인정받는 도구 |
| 포트폴리오 페이지 | Notion (우선) | 빠른 작성, 디자인 유연성, 링크 공유 용이 |

---

## 7. Convention Prerequisites

### 7.1 기존 프로젝트 Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] ESLint configuration
- [x] TypeScript configuration (`tsconfig.json`)
- [x] Python: black formatter, built-in generics convention

### 7.2 노트북 Convention (신규)

| Category | Rule |
|----------|------|
| **구조** | 문제 정의 → 데이터 로드 → EDA → 분석 → 발견 → 비즈니스 액션 |
| **셀 타입** | Markdown 셀로 각 섹션 제목 + 설명 필수 |
| **시각화** | `fig, ax` 패턴, `plt.style.use('seaborn-v0_8-whitegrid')` |
| **재현성** | 셀 순서대로 실행 시 에러 없어야 함 |

---

## 8. Implementation Order

| 순서 | 항목 | 예상 산출물 | 의존성 |
|------|------|-----------|--------|
| 1 | FR-01: 코호트 리텐션 노트북 | `notebooks/case-study-cohort-retention.ipynb` | 없음 |
| 2 | FR-02: 퍼널 분석 노트북 | `notebooks/case-study-funnel-analysis.ipynb` | 없음 |
| 3 | FR-03: README 리프레이밍 | `README.md` 수정 | FR-01, FR-02 완료 후 |
| 4 | FR-04: 포트폴리오 요약 페이지 | Notion 페이지 | FR-03 완료 후 |

---

## 9. Next Steps

1. [ ] Write design document (`portfolio-enhancement.design.md`)
2. [ ] Review and approval
3. [ ] Start implementation (FR-01 → FR-02 → FR-03 → FR-04)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-11 | Initial draft | User |
