---
name: experimentos-integrations
description: 외부 실험 플랫폼 연동 (StatsIg, GrowthBook, Hackle). Use when working with integrations, providers, external APIs, cache, retry.
---

# Integrations Skill

## 아키텍처

```
src/experimentos/integrations/
├── base.py          # BaseProvider 인터페이스
├── statsig.py       # StatsIg 연동
├── growthbook.py    # GrowthBook 연동
├── hackle.py        # Hackle 연동
├── dummy.py         # 테스트용 더미 프로바이더
├── registry.py      # Provider registry (팩토리)
├── schema.py        # 공통 스키마 (Pydantic)
├── cache.py         # 캐시 레이어
├── retry.py         # 재시도 로직
└── transform.py     # 데이터 변환
```

## Provider 인터페이스 (base.py)

모든 프로바이더는 `BaseProvider`를 상속하며 다음 메서드를 구현:
- `list_experiments()` -> 실험 목록 조회
- `fetch_experiment(id)` -> 실험 데이터 가져오기
- `transform_to_df()` -> DataFrame 변환

## 프로바이더 추가 방법

1. `src/experimentos/integrations/`에 새 파일 생성
2. `BaseProvider` 상속
3. `list_experiments()`, `fetch_experiment()` 구현
4. `registry.py`에 등록
5. `tests/test_{provider}_integration.py` 작성

## 캐시 & 재시도

- `cache.py`: API 응답 캐싱 (메모리 기반)
- `retry.py`: 실패 시 지수 백오프 재시도

## API 엔드포인트 (backend)

- `backend/routers/integrations.py`: 연동 관련 REST API
- `POST /integrations/connect` - 플랫폼 연결
- `GET /integrations/experiments` - 실험 목록
- `GET /integrations/experiments/{id}` - 실험 데이터

## 핵심 파일

- `backend/routers/integrations.py` - API 라우터
- `src/experimentos/integrations/base.py` - 인터페이스
- `src/experimentos/integrations/registry.py` - 프로바이더 팩토리
- `src/experimentos/integrations/schema.py` - 스키마 정의
