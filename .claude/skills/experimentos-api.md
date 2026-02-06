---
name: experimentos-api
description: FastAPI 백엔드 API 구조, 라우팅, 에러 핸들링. Use when working with FastAPI, endpoints, backend API, CORS, routing, error handling.
---

# API Skill

## 진입점

- `backend/main.py` - FastAPI 앱 생성, CORS 설정, 라우터 등록

## 구조

```
backend/
├── main.py           # FastAPI app, CORS, router mount, core endpoints
├── utils.py          # NumpyEncoder, sanitize 등 유틸리티
└── routers/
    └── integrations.py  # 연동 API 엔드포인트
```

## API 엔드포인트

| Method | Path | 입력 | 출력 | 설명 |
|--------|------|------|------|------|
| GET | `/` | - | `{message}` | 헬스 체크 |
| POST | `/api/health-check` | CSV file | health result + preview | 스키마 검증 + SRM |
| POST | `/api/analyze` | CSV file, guardrails? | primary + guardrails | Primary 분석 |
| POST | `/api/continuous-metrics` | CSV file | continuous results | 연속 메트릭 t-test |
| POST | `/api/bayesian-analysis` | CSV file | bayesian insights | Bayesian 분석 |
| POST | `/api/decision-memo` | JSON (DecisionMemoRequest) | decision + memo | 의사결정 메모 생성 |
| POST | `/integrations/connect` | provider, api_key | status | 연동 연결 |
| GET | `/integrations/experiments` | provider, api_key | experiment list | 실험 목록 |
| GET | `/integrations/experiment/{id}` | provider, api_key | experiment data | 실험 데이터 |

## 에러 핸들링 패턴

모든 엔드포인트는 동일한 패턴:

```python
@app.post("/api/endpoint")
async def handler(file: UploadFile = File(...)):
    # 1. 입력 검증 (400)
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        # 2. 비즈니스 로직 (src/experimentos/ 호출)
        result = business_logic(df)

        # 3. 성공 응답 (numpy 타입 직렬화)
        return sanitize({"status": "success", "result": result})

    except Exception as e:
        # 4. 서버 에러 (500)
        raise HTTPException(status_code=500, detail=str(e))
```

**핵심 규칙**:
- 400: 입력 형식 오류 (CSV가 아닌 파일 등)
- 500: 비즈니스 로직 예외 (분석 실패, 데이터 문제 등)
- `sanitize()`: numpy 타입 -> Python native 타입 변환 (JSON 직렬화)

## Numpy 직렬화

`NumpyEncoder` + `sanitize()` 함수로 numpy 타입을 JSON 직렬화:

```python
# numpy.int64, numpy.float64, numpy.bool_ -> int, float, bool
return sanitize({"status": "success", "result": result})
```

## CORS 설정

```python
allow_origins=["*"]  # 현재 전체 허용
allow_methods=["*"]
allow_headers=["*"]
```

## Pydantic 모델

```python
class DecisionMemoRequest(BaseModel):
    experiment_name: str
    health_result: dict[str, Any]
    primary_result: dict[str, Any]
    guardrail_results: list[dict[str, Any]]
    bayesian_insights: dict[str, Any] | None = None
```

## 라우터 추가 방법

1. `backend/routers/` 에 새 파일 생성
2. `APIRouter()` 생성
3. 엔드포인트 정의
4. `backend/main.py`에서 `app.include_router()` 호출

## API 컨벤션

- Pydantic 모델로 request/response 정의
- 에러 응답: `HTTPException` 사용
- 비즈니스 로직은 `src/experimentos/` 호출 (API 레이어에서 직접 구현 금지)
- JSON-serializable 응답 유지 (sanitize 함수 활용)
- File upload: `UploadFile = File(...)` 패턴

## 배포

- **Platform**: Render (Free Tier)
- **Start**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Config**: `render.yaml`

## 개발 서버

```bash
uvicorn backend.main:app --reload
```

## 환경변수

- `.env.example` 참조
- API 키: 환경변수로 관리 (코드에 하드코딩 금지)
