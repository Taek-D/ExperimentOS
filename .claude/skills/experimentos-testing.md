---
name: experimentos-testing
description: 테스트 패턴, 단위/통합 테스트, 실행 방법. Use when working with tests, pytest, test patterns, test coverage.
---

# Testing Skill

## 테스트 실행

```bash
# 전체 테스트
python -m pytest tests/ -v

# 특정 파일
python -m pytest tests/test_analysis.py -v

# 특정 테스트
python -m pytest tests/test_analysis.py::test_name -v

# 상세 출력
python -m pytest tests/ -v --tb=long
```

## 테스트 구조

```
tests/
├── test_analysis.py                    # 전환율 분석 테스트
├── test_analysis_multivariant_overall.py  # 다변량 분석
├── test_multiple_comparisons.py        # 다중 비교 보정
├── test_healthcheck_multivariant.py    # 헬스체크 다변량
├── test_integration_service.py         # 통합 서비스
├── test_integration_cache_retry.py     # 캐시/재시도
├── test_integrations.py               # 통합 전반
├── test_statsig_*.py                   # StatsIg 연동
├── test_growthbook_integration.py      # GrowthBook 연동
├── test_hackle_provider_contract.py    # Hackle 연동
└── test_api_statsig_integration.py     # API 통합
```

## 테스트 작성 규칙

### Decision Regression 테스트
- 기존 decision 테스트는 절대 수정하지 않음
- 새 기능이 decision branching을 변경하면 안 됨

### Bayesian 테스트
- RNG seed 고정: `numpy.random.default_rng(42)`
- tight assertion 금지, threshold/monotonic assertion 사용
- 예: `assert prob_b_better > 0.5` (not `assert prob_b_better == 0.73`)

### 일반 규칙
- 모든 public 함수에 최소 1개 테스트
- edge case 테스트: 0 users, negative values, missing columns
- 테스트 데이터는 테스트 함수 내에서 직접 생성 (fixture 최소화)

## 자주 사용하는 명령어

```bash
python -m pytest tests/ -v                          # 전체
python -m pytest tests/test_analysis.py -v           # 분석
python -m pytest tests/ -k "healthcheck" -v          # 키워드 필터
python -m pytest tests/ --tb=short -q                # 간단 출력
```
