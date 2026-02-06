# Lint & Fix

Python과 TypeScript 코드의 린트 검사 및 자동 수정을 실행합니다.

## 수행 작업

### Python

1. `black --line-length 100 src/ backend/ tests/` 포맷팅
2. `pylint src/ backend/` 린트 검사
3. `mypy src/ backend/` 타입 검사
4. 발견된 문제 요약 및 수정 제안

### TypeScript (experimentos-guardrails)

1. `cd experimentos-guardrails && npm run lint` 실행
2. 발견된 문제 요약 및 수정 제안

## 인수

- $ARGUMENTS: `python`, `typescript`, `all` (기본값: `all`)
