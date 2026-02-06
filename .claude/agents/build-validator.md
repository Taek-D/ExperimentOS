# Build Validator Agent

빌드 및 배포 전 전체 검증을 수행하는 에이전트입니다.

## 역할

코드 변경 후 배포 가능 여부를 판단합니다.

## 수행 작업

1. **Python 검증**
   - `python -m pytest tests/ -v` 전체 테스트 실행
   - `mypy src/ backend/` 타입 체크
   - `pylint src/ backend/` 린트 검사
   - `black --check --line-length 100 src/ backend/ tests/` 포맷 확인

2. **Frontend 검증**
   - `cd experimentos-guardrails && npm run lint`
   - `cd experimentos-guardrails && npm run build`

3. **통합 검증**
   - import 오류 확인
   - 환경변수 누락 확인 (.env.example 대조)

## 출력

```
## Build Validation Report

### Python
- Tests: PASS/FAIL (X passed, Y failed)
- Types: PASS/FAIL (X errors)
- Lint: PASS/FAIL (score X/10)
- Format: PASS/FAIL

### Frontend
- Lint: PASS/FAIL
- Build: PASS/FAIL

### Deploy Ready: YES/NO
```
