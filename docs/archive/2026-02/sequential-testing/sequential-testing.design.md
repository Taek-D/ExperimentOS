# Sequential Testing Design Document

> Feature: 실험 조기 종료 (Sequential Testing / Group Sequential Design)
> Status: Design
> Created: 2026-02-10
> References: `docs/01-plan/plan-v1.md` Section 4.1 Feature 1

---

## 1. 개요

### 1.1 목표
실험 진행 중 데이터가 축적될 때마다(look) 통계적으로 안전하게 **조기 종료** 여부를 판단하여,
실험 기간을 평균 30% 단축하면서도 Type I Error를 목표 alpha 수준으로 통제한다.

### 1.2 핵심 가치
- **실험 기간 단축**: 효과가 확실할 때 조기 Launch/Rollback 가능
- **Type I Error 통제**: Alpha spending으로 peek penalty 없이 중간 확인 가능
- **기존 파이프라인과 통합**: 현재 Decision Framework에 자연스럽게 연결

### 1.3 비목표 (Non-goals)
- Always-valid p-value (mSPRT/GROW) — Phase 3 고려
- 연속 모니터링 (Continuous monitoring) — 별도 설계 필요
- Adaptive sample size re-estimation — 복잡도 높아 제외

---

## 2. 이론적 배경

### 2.1 Group Sequential Design (GSD)
미리 정한 K번의 분석 시점(looks)에서 중간 분석을 수행하고,
각 시점마다 조정된 기각 경계(boundary)를 사용하여 Type I Error를 alpha 수준으로 통제한다.

### 2.2 Alpha Spending Function
Lan-DeMets approach: alpha를 information fraction에 따라 점진적으로 소비한다.

```
α*(t) = alpha spending function at information fraction t ∈ [0, 1]

Information fraction: t_k = n_k / N_max  (현재까지 수집된 샘플 / 최대 계획 샘플)
```

### 2.3 지원할 Boundary 함수

| Boundary | 특성 | 사용 사례 |
|----------|------|----------|
| **O'Brien-Fleming (OBF)** | 초반 엄격, 후반 완화 | 실무 표준 (권장 기본값) |
| **Pocock** | 모든 look에서 동일 기준 | 초반 peek 가능성 높일 때 |
| **Custom alpha spending** | 사용자 정의 | 고급 사용자용 |

### 2.4 O'Brien-Fleming Alpha Spending Function

```python
# Lan-DeMets approximation of OBF:
α*(t) = 2 - 2 * Φ(z_{α/2} / √t)

# 여기서:
# t = information fraction (0, 1]
# Φ = standard normal CDF
# z_{α/2} = 1.96 for α = 0.05
```

### 2.5 Pocock Alpha Spending Function

```python
# Lan-DeMets approximation of Pocock:
α*(t) = α * ln(1 + (e - 1) * t)
```

---

## 3. 기술 설계

### 3.1 새 모듈: `src/experimentos/sequential.py`

```python
"""
Sequential Testing Module

Group Sequential Design을 사용한 실험 조기 종료 판단.
Lan-DeMets alpha spending approach를 사용합니다.
"""

from dataclasses import dataclass
from scipy.stats import norm
import numpy as np
from .config import config


@dataclass
class SequentialConfig:
    """Sequential testing 설정."""
    max_looks: int = 5
    """최대 중간 분석 횟수"""

    alpha: float = 0.05
    """전체 유의수준"""

    boundary_type: str = "obrien_fleming"
    """경계 함수 타입: 'obrien_fleming', 'pocock', 'custom'"""

    power: float = 0.8
    """목표 검정력"""

    one_sided: bool = False
    """단측 검정 여부 (기본: 양측)"""


SEQUENTIAL_CONFIG = SequentialConfig()
```

### 3.2 핵심 함수 설계

#### 3.2.1 Alpha Spending 계산

```python
def alpha_spending(
    info_fraction: float,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
) -> float:
    """
    Lan-DeMets alpha spending function.

    Args:
        info_fraction: Information fraction t ∈ (0, 1]
        alpha: Overall significance level
        boundary_type: "obrien_fleming" | "pocock"

    Returns:
        float: Cumulative alpha spent at this information fraction
    """
```

#### 3.2.2 경계값 계산

```python
def calculate_boundaries(
    max_looks: int,
    info_fractions: list[float] | None = None,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
) -> list[dict[str, float]]:
    """
    각 look에서의 기각 경계값을 계산한다.

    Args:
        max_looks: 총 분석 횟수 K
        info_fractions: 각 look의 information fraction [t1, t2, ..., tK]
                       None이면 균등 분할 [1/K, 2/K, ..., 1.0]
        alpha: 전체 유의수준
        boundary_type: 경계 함수

    Returns:
        list[dict]: [{
            "look": int,
            "info_fraction": float,
            "z_boundary": float,        # 기각 경계 z-값
            "alpha_spent": float,        # 해당 look에서 소비한 alpha
            "cumulative_alpha": float,   # 누적 alpha 소비량
        }, ...]
    """
```

#### 3.2.3 조기 종료 판정

```python
def check_sequential(
    z_stat: float,
    current_look: int,
    max_looks: int,
    info_fraction: float,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
    previous_looks: list[dict] | None = None,
) -> dict[str, object]:
    """
    현재 look에서 조기 종료 가능 여부를 판단한다.

    Args:
        z_stat: 현재 z-test statistic
        current_look: 현재 분석 번호 (1-indexed)
        max_looks: 총 계획된 분석 횟수
        info_fraction: 현재 information fraction
        alpha: 전체 유의수준
        boundary_type: 경계 함수
        previous_looks: 이전 look 결과 목록 (alpha spending 계산용)

    Returns:
        dict: {
            "can_stop": bool,           # 조기 종료 가능 여부
            "decision": str,            # "reject_null" | "continue" | "fail_to_reject"
            "z_stat": float,
            "z_boundary": float,
            "alpha_spent_this_look": float,
            "cumulative_alpha_spent": float,
            "info_fraction": float,
            "current_look": int,
            "max_looks": int,
            "message": str,             # 사용자 친화적 메시지
        }
    """
```

#### 3.2.4 Sequential 분석 통합 함수

```python
def analyze_sequential(
    control_users: int,
    control_conversions: int,
    treatment_users: int,
    treatment_conversions: int,
    target_sample_size: int,
    current_look: int,
    max_looks: int,
    alpha: float = 0.05,
    boundary_type: str = "obrien_fleming",
    previous_looks: list[dict] | None = None,
) -> dict[str, object]:
    """
    Sequential Analysis 통합 실행.

    1. Information fraction 계산
    2. Z-test statistic 계산 (기존 analysis.py 로직 재사용)
    3. check_sequential 호출
    4. Boundary 시각화용 데이터 반환

    Returns:
        dict: {
            "sequential_result": dict,  # check_sequential 결과
            "primary_result": dict,     # 기존 primary 분석 결과
            "boundaries": list[dict],   # 전체 boundary 데이터
            "progress": {
                "current_sample": int,
                "target_sample": int,
                "info_fraction": float,
                "estimated_completion": str | None,
            }
        }
    """
```

### 3.3 Config 확장

`src/experimentos/config.py`에 sequential 관련 설정 추가:

```python
@dataclass
class ExperimentConfig:
    # ... 기존 설정 ...

    # ===== Sequential Testing Settings =====
    SEQUENTIAL_MAX_LOOKS: int = 5
    """기본 최대 중간 분석 횟수"""

    SEQUENTIAL_BOUNDARY_TYPE: str = "obrien_fleming"
    """기본 경계 함수 타입"""

    SEQUENTIAL_ENABLED: bool = True
    """Sequential testing 기능 활성화"""
```

---

## 4. API 설계

### 4.1 새 엔드포인트

#### `POST /api/sequential-analysis`

Sequential 분석을 실행한다.

**Request Body** (JSON):
```json
{
    "control_users": 5000,
    "control_conversions": 600,
    "treatment_users": 5100,
    "treatment_conversions": 680,
    "target_sample_size": 20000,
    "current_look": 2,
    "max_looks": 5,
    "alpha": 0.05,
    "boundary_type": "obrien_fleming",
    "previous_looks": [
        {
            "look": 1,
            "z_stat": 1.2,
            "info_fraction": 0.2,
            "cumulative_alpha_spent": 0.0001
        }
    ]
}
```

**Response**:
```json
{
    "status": "success",
    "sequential_result": {
        "can_stop": false,
        "decision": "continue",
        "z_stat": 1.85,
        "z_boundary": 2.96,
        "alpha_spent_this_look": 0.003,
        "cumulative_alpha_spent": 0.0031,
        "info_fraction": 0.4,
        "current_look": 2,
        "max_looks": 5,
        "message": "현재 데이터로는 결론을 내릴 수 없습니다. 추가 데이터 수집이 필요합니다."
    },
    "primary_result": {
        "control_rate": 0.12,
        "treatment_rate": 0.1333,
        "absolute_lift": 0.0133,
        "relative_lift": 0.111,
        "p_value": 0.064,
        "is_significant": false
    },
    "boundaries": [
        {"look": 1, "info_fraction": 0.2, "z_boundary": 4.56},
        {"look": 2, "info_fraction": 0.4, "z_boundary": 2.96},
        {"look": 3, "info_fraction": 0.6, "z_boundary": 2.36},
        {"look": 4, "info_fraction": 0.8, "z_boundary": 2.06},
        {"look": 5, "info_fraction": 1.0, "z_boundary": 1.98}
    ],
    "progress": {
        "current_sample": 10100,
        "target_sample": 20000,
        "info_fraction": 0.505,
        "percentage": 50.5
    }
}
```

#### `GET /api/sequential-boundaries`

경계값만 조회한다 (시각화/계획용).

**Query Parameters**:
- `max_looks` (int, default: 5)
- `alpha` (float, default: 0.05)
- `boundary_type` (str, default: "obrien_fleming")

**Response**:
```json
{
    "boundaries": [
        {"look": 1, "info_fraction": 0.2, "z_boundary": 4.56, "p_boundary": 0.000005},
        {"look": 2, "info_fraction": 0.4, "z_boundary": 2.96, "p_boundary": 0.003},
        ...
    ],
    "config": {
        "max_looks": 5,
        "alpha": 0.05,
        "boundary_type": "obrien_fleming"
    }
}
```

### 4.2 Pydantic Models

```python
class SequentialAnalysisRequest(BaseModel):
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int
    target_sample_size: int
    current_look: int
    max_looks: int = 5
    alpha: float = 0.05
    boundary_type: str = "obrien_fleming"
    previous_looks: list[dict[str, float]] | None = None
```

---

## 5. Frontend 설계

### 5.1 새 컴포넌트

#### `SequentialMonitor.tsx`

Sequential testing 대시보드 컴포넌트.

**Props**:
```typescript
interface SequentialMonitorProps {
    sequentialResult: SequentialResult | null;
    boundaries: BoundaryPoint[];
    progress: SequentialProgress;
    onRunAnalysis: (params: SequentialParams) => void;
}
```

**UI 구성**:
```
┌─────────────────────────────────────────────────┐
│ Sequential Testing Monitor                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  Progress: ████████░░░░░░░ 50.5% (Look 2/5)    │
│                                                  │
│  Decision: ⏳ Continue collecting data           │
│                                                  │
│  ┌─ Boundary Chart ──────────────────────┐      │
│  │  z                                     │      │
│  │  5 ┤  ●                               │      │
│  │  4 ┤   ╲                              │      │
│  │  3 ┤    ╲  ★ (current z=1.85)         │      │
│  │  2 ┤     ╲____╲______                 │      │
│  │  1 ┤                  ───────         │      │
│  │  0 ┼────┼────┼────┼────┼───→ fraction │      │
│  │    0.2  0.4  0.6  0.8  1.0            │      │
│  └───────────────────────────────────────┘      │
│                                                  │
│  Look History:                                   │
│  ┌──────┬──────────┬────────┬──────────┐        │
│  │ Look │ Fraction │ z-stat │ Boundary │        │
│  ├──────┼──────────┼────────┼──────────┤        │
│  │  1   │  0.20    │  1.20  │  4.56    │        │
│  │  2   │  0.40    │  1.85  │  2.96    │        │
│  └──────┴──────────┴────────┴──────────┘        │
│                                                  │
│  [Update Analysis]                               │
└─────────────────────────────────────────────────┘
```

#### `charts/BoundaryChart.tsx`

Sequential boundary 시각화 차트.

```typescript
interface BoundaryChartProps {
    boundaries: BoundaryPoint[];
    currentLook: {
        infoFraction: number;
        zStat: number;
    } | null;
    previousLooks: {
        infoFraction: number;
        zStat: number;
    }[];
}
```

- Recharts `LineChart`로 구현
- OBF/Pocock boundary 곡선
- 현재 look 위치 표시 (별 마커)
- 이전 look 히스토리 (점 마커)
- Boundary 위 영역: 빨간색 (기각 영역)
- Boundary 아래 영역: 녹색 (계속 영역)

### 5.2 TypeScript 타입 정의

```typescript
// types.ts 확장

interface SequentialResult {
    can_stop: boolean;
    decision: "reject_null" | "continue" | "fail_to_reject";
    z_stat: number;
    z_boundary: number;
    alpha_spent_this_look: number;
    cumulative_alpha_spent: number;
    info_fraction: number;
    current_look: number;
    max_looks: number;
    message: string;
}

interface BoundaryPoint {
    look: number;
    info_fraction: number;
    z_boundary: number;
    p_boundary?: number;
    alpha_spent?: number;
    cumulative_alpha?: number;
}

interface SequentialProgress {
    current_sample: number;
    target_sample: number;
    info_fraction: number;
    percentage: number;
}

interface SequentialParams {
    controlUsers: number;
    controlConversions: number;
    treatmentUsers: number;
    treatmentConversions: number;
    targetSampleSize: number;
    currentLook: number;
    maxLooks: number;
    alpha: number;
    boundaryType: "obrien_fleming" | "pocock";
    previousLooks?: Array<{
        look: number;
        z_stat: number;
        info_fraction: number;
        cumulative_alpha_spent: number;
    }>;
}
```

### 5.3 네비게이션 통합

`Sidebar.tsx`에 "Sequential Monitor" 메뉴 항목 추가:

```
Dashboard
Power Calculator
Sequential Monitor  ← NEW
Integration
```

`App.tsx`에서 `currentPage === "sequential"` 분기 추가.

### 5.4 Power Calculator 확장

`PowerCalculator.tsx`에 sequential 옵션 추가:
- "Sequential Testing 사용" 토글
- Max Looks 입력 (기본: 5)
- Boundary Type 선택 (OBF / Pocock)
- Sequential 사용 시 adjusted sample size 표시 (inflation factor)

---

## 6. Decision Framework 통합

### 6.1 기존 Decision Flow와의 관계

Sequential testing은 기존 Decision Framework를 **대체하지 않고 보완**한다.

```
[Sequential Analysis]
    ↓ can_stop = true, decision = "reject_null"
[기존 Decision Framework 실행]
    health check → primary → guardrails → make_decision()
    ↓
[Decision Memo] (+ sequential 컨텍스트 추가)
```

### 6.2 Memo 확장

Sequential testing이 활성화된 경우 Decision Memo에 추가 정보:

```markdown
## Sequential Testing Summary

- **Boundary Type**: O'Brien-Fleming
- **Current Look**: 3 / 5
- **Information Fraction**: 60%
- **Z-statistic**: 2.45 (Boundary: 2.36)
- **Status**: Early stopping justified
- **Alpha Spent**: 0.012 / 0.05
- **Note**: Type I Error rate is controlled at α = 0.05 across all looks.
```

### 6.3 Decision Rules 확장 (memo.py)

```python
# memo.py 확장 (기존 로직 변경 없음, 추가만)

def make_decision(health, primary, guardrails, sequential=None):
    """
    sequential 파라미터가 제공되면:
    - sequential.can_stop = False → 무조건 Hold ("추가 데이터 수집 필요")
    - sequential.can_stop = True → 기존 decision 로직 실행
    """
```

---

## 7. 파일 구조

### 7.1 새로 생성할 파일

```
src/experimentos/
└── sequential.py                    # Sequential testing 핵심 로직

backend/
└── main.py                          # 엔드포인트 추가 (기존 파일 수정)

experimentos-guardrails/
├── components/
│   ├── SequentialMonitor.tsx         # Sequential 대시보드
│   └── charts/
│       └── BoundaryChart.tsx         # Boundary 시각화
├── types.ts                         # Sequential 타입 추가 (기존 파일 수정)
└── api/client.ts                    # API 함수 추가 (기존 파일 수정)

tests/
├── test_sequential.py               # 핵심 로직 테스트
└── test_sequential_boundaries.py    # Boundary 계산 정확도 테스트
```

### 7.2 수정할 기존 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/experimentos/config.py` | `SEQUENTIAL_*` 설정 추가 |
| `src/experimentos/memo.py` | `make_decision()` sequential 파라미터 추가 (optional, 하위 호환) |
| `backend/main.py` | 2개 엔드포인트 추가 |
| `experimentos-guardrails/App.tsx` | Sequential 페이지 라우팅 추가 |
| `experimentos-guardrails/components/Sidebar.tsx` | 메뉴 항목 추가 |
| `experimentos-guardrails/components/PowerCalculator.tsx` | Sequential 옵션 추가 |
| `experimentos-guardrails/types.ts` | Sequential 타입 정의 추가 |
| `experimentos-guardrails/api/client.ts` | API 함수 추가 |

---

## 8. 테스트 설계

### 8.1 단위 테스트 (`test_sequential.py`)

| 테스트 | 설명 |
|--------|------|
| `test_alpha_spending_obf_at_zero` | t=0에서 alpha_spent = 0 |
| `test_alpha_spending_obf_at_one` | t=1에서 alpha_spent = alpha |
| `test_alpha_spending_obf_monotonic` | alpha spending 단조 증가 |
| `test_alpha_spending_pocock_at_one` | Pocock t=1에서 alpha |
| `test_alpha_spending_pocock_monotonic` | Pocock 단조 증가 |
| `test_boundaries_count_matches_looks` | boundary 개수 = max_looks |
| `test_obf_early_boundaries_stricter` | OBF 초반 z-boundary > 후반 |
| `test_pocock_boundaries_roughly_equal` | Pocock boundary 균등 |
| `test_check_sequential_reject` | z > boundary → can_stop = True |
| `test_check_sequential_continue` | z < boundary → continue |
| `test_check_sequential_final_look` | 마지막 look에서 fail_to_reject |
| `test_analyze_sequential_integration` | 통합 함수 전체 흐름 |

### 8.2 경계값 정확도 테스트 (`test_sequential_boundaries.py`)

검증된 참조값과 비교 (Jennison & Turnbull, 2000):

| OBF (K=5, α=0.05) | 참조 z-boundary |
|---------------------|----------------|
| Look 1 (t=0.2) | ~4.56 |
| Look 2 (t=0.4) | ~2.96 |
| Look 3 (t=0.6) | ~2.36 |
| Look 4 (t=0.8) | ~2.06 |
| Look 5 (t=1.0) | ~1.98 |

- 허용 오차: 0.05 (alpha spending 근사치 특성)
- tight assertion 금지 (근사 알고리즘)

### 8.3 Decision Regression 보호

- 기존 `test_decision.py`, `test_decision_branches.py` 반드시 통과
- `sequential=None`이면 기존 동작과 100% 동일해야 함
- 새 테스트 파일에서만 sequential 파라미터 테스트

---

## 9. 구현 순서

```
Phase 1: 핵심 로직 (Backend)
├── Step 1: config.py에 SEQUENTIAL_* 설정 추가
├── Step 2: sequential.py 핵심 함수 구현
│   ├── alpha_spending()
│   ├── calculate_boundaries()
│   └── check_sequential()
├── Step 3: analyze_sequential() 통합 함수
├── Step 4: test_sequential.py 작성 및 통과
└── Step 5: test_sequential_boundaries.py 작성 및 통과

Phase 2: API 연동 (Backend)
├── Step 6: Pydantic models 정의
├── Step 7: POST /api/sequential-analysis 엔드포인트
├── Step 8: GET /api/sequential-boundaries 엔드포인트
└── Step 9: memo.py make_decision() sequential 파라미터 추가

Phase 3: Frontend
├── Step 10: types.ts Sequential 타입 추가
├── Step 11: api/client.ts API 함수 추가
├── Step 12: BoundaryChart.tsx 차트 구현
├── Step 13: SequentialMonitor.tsx 컴포넌트 구현
├── Step 14: Sidebar + App.tsx 라우팅 추가
└── Step 15: PowerCalculator.tsx sequential 옵션 추가

Phase 4: 통합 검증
├── Step 16: 기존 decision regression 테스트 확인
├── Step 17: Frontend 빌드 확인
└── Step 18: E2E 흐름 수동 검증
```

---

## 10. 의존성

### 10.1 Python 의존성
- `scipy.stats.norm` — 이미 설치됨 (scipy 1.11+)
- `numpy` — 이미 설치됨
- **추가 패키지 없음**

### 10.2 Frontend 의존성
- `recharts` — 이미 설치됨 (LineChart 사용)
- **추가 패키지 없음**

---

## 11. 리스크 및 완화

| 리스크 | 영향 | 완화 |
|--------|------|------|
| Alpha spending 근사 오차 | 실제 Type I Error > alpha | 보수적 참조값 테스트 + 문서에 근사치 명시 |
| 기존 decision 로직 변경 | 2-variant regression | sequential=None 기본값으로 하위 호환 보장 |
| 사용자 오용 (너무 많은 looks) | Alpha 낭비 | max_looks 제한 (기본 5, 최대 20) + 경고 메시지 |
| Boundary 시각화 오해 | 잘못된 의사결정 | 각 look 설명 + 가이드 투어 tooltip |

---

*문서 버전: v1.0*
*최종 수정: 2026-02-10*
*작성: Claude Code (PDCA Design)*
