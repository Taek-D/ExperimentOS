# Typecheck All

전체 프로젝트 타입 체크를 실행합니다.

## 수행 작업

### Python

1. `mypy src/ backend/` 실행
2. 타입 오류 목록 정리
3. 수정 제안

### TypeScript

1. `cd experimentos-guardrails && npx tsc --noEmit` 실행
2. 타입 오류 목록 정리
3. 수정 제안

## 결과

- 파일별 타입 오류 요약
- 오류 심각도 분류 (error / warning)
- 수정 방법 제안
