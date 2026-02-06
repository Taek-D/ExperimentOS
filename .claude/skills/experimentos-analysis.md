---
name: experimentos-analysis
description: 통계 분석 모듈 (전환율, 연속 메트릭, Bayesian, 검정력). Use when working with statistical analysis, z-test, t-test, bayesian, power calculation, SRM, guardrails, decision.
---

# Analysis Skill

## Decision Tree (memo.py)

`make_decision(health, primary, guardrails)` -> Launch / Hold / Rollback

```
Rule 1: health.overall_status == "Blocked"
  -> Hold ("데이터 품질 문제")

Rule 2: srm.status in ["Warning", "Blocked"]
  -> Hold ("SRM 탐지")

Rule 3: primary.is_significant AND any guardrail.severe
  -> Rollback ("심각한 Guardrail 악화")

Rule 4: primary.is_significant AND any guardrail.worsened
  -> Hold ("Guardrail 악화")

Rule 5: primary.is_significant AND no guardrail issues
  -> Launch ("Primary 유의, Guardrail 정상")

Rule 6: NOT primary.is_significant
  -> Hold ("Primary 비유의")
```

**우선순위**: Rule 1 > 2 > 3 > 4 > 5 > 6 (위에서부터 first-match)

## Guardrail 판정 기준 (config.py)

| 판정 | 조건 | config 값 |
|------|------|-----------|
| OK | delta < 0.1%p | `GUARDRAIL_WORSENED_THRESHOLD = 0.001` |
| Worsened | 0.1%p <= delta < 0.3%p | `GUARDRAIL_WORSENED_THRESHOLD = 0.001` |
| Severe | delta >= 0.3%p | `GUARDRAIL_SEVERE_THRESHOLD = 0.003` |

## SRM 판정 기준 (config.py)

| 판정 | 조건 | config 값 |
|------|------|-----------|
| Healthy | p >= 0.001 | - |
| Warning | 0.00001 <= p < 0.001 | `SRM_WARNING_THRESHOLD = 0.001` |
| Blocked | p < 0.00001 | `SRM_BLOCKED_THRESHOLD = 0.00001` |

## 핵심 모듈

### analysis.py - 분석 오케스트레이터
- `calculate_primary(df)`: 전환율 primary 분석 (Two-proportion z-test)
- `calculate_guardrails(df)`: Guardrail 메트릭 분석 (delta 계산 -> worsened/severe 판정)
- `calculate_continuous_metrics(df)`: 연속 메트릭 분석
- `calculate_bayesian_insights(df, continuous)`: Bayesian 인사이트

### healthcheck.py - 데이터 검증
- `validate_schema(df)`: 필수 컬럼, 타입, 범위, 중복 검증
- `detect_srm(variants_data, expected_split)`: N-variant SRM (chi-square test)
  - **시그니처**: `detect_srm(variants_data: dict[str, int], expected_split=None, ...)`
  - 2-variant 예: `detect_srm({"control": 10000, "treatment": 10000}, [50, 50])`
- `run_health_check(df, expected_split)`: Schema + SRM 통합 실행
- Status: `Healthy` / `Warning` / `Blocked`

### continuous_analysis.py - 연속 메트릭
- Welch's t-test from sufficient statistics
- 분산 추정: `s^2 = (sum_sq - sum^2/n) / (n-1)`
- Edge cases: n < 2, variance <= 0

### bayesian.py - Bayesian 분석
- Beta-Binomial 모델 (전환율)
- Continuous posterior simulation
- `numpy.random.default_rng(seed)` 사용
- **설명용만** - decision 로직에 영향 없음

### power.py - 검정력 계산
- Sample size calculator (statsmodels NormalIndPower)
- Conversion & continuous metric 지원

### memo.py - 의사결정 + 메모 생성
- `make_decision()`: Decision tree (위 참조)
- `generate_memo()`: 1pager Markdown 생성
- `export_html()`: Markdown -> HTML 변환

## 설정 (config.py)

`ExperimentConfig` dataclass (singleton: `config`):

| 필드 | 기본값 | 설명 |
|------|--------|------|
| `SIGNIFICANCE_ALPHA` | 0.05 | 유의수준 |
| `SRM_WARNING_THRESHOLD` | 0.001 | SRM Warning 기준 |
| `SRM_BLOCKED_THRESHOLD` | 0.00001 | SRM Blocked 기준 |
| `GUARDRAIL_WORSENED_THRESHOLD` | 0.001 | Guardrail Worsened (0.1%p) |
| `GUARDRAIL_SEVERE_THRESHOLD` | 0.003 | Guardrail Severe (0.3%p) |
| `MULTIPLE_TESTING_METHOD` | "bonferroni" | 다중 비교 보정 |
| `VAR_TOLERANCE` | 1e-9 | 분산 부동소수점 허용치 |
| `BAYES_SAMPLES` | 10000 | Bayesian 시뮬레이션 수 |
| `BAYES_SEED` | 42 | Bayesian RNG seed |

## CSV Schema

### Required
- `variant`: "control" 필수 포함 + 1개 이상 treatment
- `users`: 노출 사용자 수 (양의 정수)
- `conversions`: 전환 사용자 수 (0 <= conversions <= users)

### Optional (continuous)
- `{metric}_sum`, `{metric}_sum_sq`: 연속 메트릭 pair
- 예: `revenue_sum`, `revenue_sum_sq`

### Optional (guardrail)
- `{metric}_count` 형태의 컬럼: 자동 감지 대상
