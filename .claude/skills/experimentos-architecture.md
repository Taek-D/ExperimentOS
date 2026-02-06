---
name: experimentos-architecture
description: ExperimentOS 전체 아키텍처, 폴더 구조, 의존성 방향. Use when working with project structure, module boundaries, data flow.
---

# Architecture Skill

## 프로젝트 개요

ExperimentOS는 A/B 테스트 의사결정 플랫폼입니다. 헬스체크, 통계 분석, Bayesian 인사이트, 의사결정 메모를 자동 생성합니다.

## 레이어 구조

```
[UI Layer]
├── pages/ (Streamlit)           # 로컬 UI
├── experimentos-guardrails/ (React)  # 웹 UI
└── backend/ (FastAPI)           # API 서버

    ↓ 호출

[Business Logic Layer]
└── src/experimentos/            # 도메인 로직 (stateless)
    ├── config.py                # 설정 (single source of truth)
    ├── healthcheck.py           # 데이터 검증
    ├── analysis.py              # 분석 오케스트레이터
    ├── continuous_analysis.py   # 연속 메트릭 분석
    ├── bayesian.py              # Bayesian 시뮬레이션
    ├── memo.py                  # 의사결정 메모
    ├── power.py                 # 검정력 계산
    └── integrations/            # 외부 플랫폼 연동
```

## 데이터 흐름

```
CSV Upload → healthcheck.py → analysis.py → memo.py → Decision Memo
                                  ↓
                          bayesian.py (설명용)
                          continuous_analysis.py
```

## 핵심 원칙

1. **src/experimentos/**는 Streamlit 의존성 최소화 (state.py, logger.py 예외)
2. **Decision은 frequentist 기반**: make_decision()은 healthcheck + primary + guardrails만 사용
3. **Bayesian은 설명용**: 의사결정 로직에 절대 영향 없음
4. **config.py가 single source of truth**: 모든 threshold/tolerance 여기서 관리

## 핵심 파일

- `src/experimentos/config.py` - 모든 설정값
- `src/experimentos/analysis.py` - 분석 오케스트레이터
- `src/experimentos/memo.py` - 의사결정 규칙 엔진
- `backend/main.py` - FastAPI 진입점
- `app.py` - Streamlit 진입점
- `ARCHITECTURE.md` - 상세 아키텍처 문서
