# Build All

전체 프로젝트 빌드를 실행합니다.

## 수행 작업

### Backend (Python)

1. 의존성 확인: `pip install -r requirements.txt`
2. 타입 체크: `mypy src/ backend/`
3. 테스트: `python -m pytest tests/ -v`

### Frontend (React)

1. 의존성 확인: `cd experimentos-guardrails && npm install`
2. 린트: `npm run lint`
3. 빌드: `npm run build`

## 결과

- 각 단계별 성공/실패 여부 보고
- 실패 시 원인 분석 및 수정 가이드 제공
