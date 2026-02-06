# Test Module

특정 모듈 또는 전체 테스트를 실행합니다.

## 사용법

```
/test-module [모듈명]
```

- 인수 없음: 전체 테스트 실행
- 모듈명 지정: 해당 모듈 테스트만 실행

## 수행 작업

1. 인수 확인: $ARGUMENTS
2. 인수가 있으면 해당 모듈 테스트 파일 찾기
3. `python -m pytest tests/test_{module}.py -v` 실행
4. 실패한 테스트가 있으면 원인 분석 및 수정 제안
5. 전체 결과 요약 출력

## 예시

- `/test-module analysis` → `python -m pytest tests/test_analysis.py -v`
- `/test-module` → `python -m pytest tests/ -v`
- `/test-module integrations` → `python -m pytest tests/test_integration*.py -v`
