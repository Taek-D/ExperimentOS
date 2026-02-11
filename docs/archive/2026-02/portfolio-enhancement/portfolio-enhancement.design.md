# Portfolio Enhancement Design Document

> **Summary**: 데이터 분석가 포트폴리오 포지셔닝 강화 — 코호트/퍼널 노트북 + README 리프레이밍
>
> **Project**: ExperimentOS
> **Author**: User
> **Date**: 2026-02-11
> **Status**: Draft
> **Planning Doc**: [portfolio-enhancement.plan.md](../../01-plan/features/portfolio-enhancement.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **분석 역량 시연**: 코호트 리텐션 + 퍼널 분석을 통해 DA 핵심 스킬 증명
2. **데이터 다양성**: 기존 마케팅 데이터 외 e-commerce 트랜잭션 데이터로 분석 폭 확장
3. **스토리 일관성**: 모든 노트북이 "문제 → 분석 → 발견 → 비즈니스 액션" 구조 유지
4. **포트폴리오 가독성**: README에서 노트북(분석 결과)을 전면에 배치

### 1.2 Design Principles

- **실데이터 우선**: 합성 데이터 대신 Kaggle 공개 데이터셋 사용
- **재현 가능성**: 모든 노트북 `jupyter nbconvert --execute` 통과
- **비즈니스 연결**: 모든 분석에 매출/비용 임팩트 수치 포함
- **기존 코드 무영향**: notebooks/ 디렉토리에 격리, 테스트 영향 없음

---

## 2. 데이터 설계

### 2.1 데이터셋 선택

기존 마케팅 A/B 테스트 데이터(588K)에는 **타임스탬프와 퍼널 단계가 없어** 코호트/퍼널 분석이 불가합니다.

| 분석 | 필요 데이터 | 기존 데이터 | 대안 |
|------|-----------|-----------|------|
| 코호트 리텐션 | 유저별 가입일 + 일별 활동 이력 | ❌ 없음 | 공개 데이터셋 사용 |
| 퍼널 분석 | 유저별 다단계 이벤트 (view→cart→purchase) | ❌ 없음 (0/1 전환만 존재) | 공개 데이터셋 사용 |

**선정 데이터셋**:

| 노트북 | 데이터셋 | 출처 | 크기 | 라이선스 |
|--------|---------|------|------|----------|
| 코호트 리텐션 | Online Retail Dataset (UCI) | [Kaggle](https://www.kaggle.com/datasets/carrie1/ecommerce-data) | 541K rows, 8 columns | CC BY 4.0 |
| 퍼널 분석 | eCommerce Events (Kaggle) | [Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop) | 20M+ events | CC0 |

### 2.2 데이터 스키마

#### 코호트 리텐션 데이터 (Online Retail)

```
InvoiceNo   : 거래 번호 (C로 시작하면 취소)
StockCode   : 상품 코드
Description : 상품명
Quantity    : 수량
InvoiceDate : 거래 일시 (YYYY-MM-DD HH:MM)
UnitPrice   : 단가
CustomerID  : 고객 ID (일부 결측)
Country     : 국가
```

**파생 변수**:
- `cohort_month`: 고객별 첫 구매 월 (YYYY-MM)
- `order_month`: 거래 월
- `cohort_index`: (order_month - cohort_month) in months
- `revenue`: Quantity * UnitPrice

#### 퍼널 분석 데이터 (eCommerce Events)

```
event_time    : 이벤트 발생 시각 (UTC)
event_type    : view / cart / purchase
product_id    : 상품 ID
category_code : 카테고리
brand         : 브랜드
price         : 가격
user_id       : 유저 ID
user_session  : 세션 ID
```

**퍼널 단계**: `view → cart → purchase`

---

## 3. FR-01: 코호트 리텐션 분석 노트북

### 3.1 파일 정보

- **파일명**: `notebooks/case-study-cohort-retention.ipynb`
- **데이터**: Online Retail Dataset (UCI) — `notebooks/online_retail.csv`
- **예상 셀 수**: 18-22 cells

### 3.2 노트북 구조

```
1. [MD]  제목 + 요약 + 분석 구조
2. [CODE] 라이브러리 import + 데이터 로드
3. [MD]  Section 1: 탐색적 데이터 분석
4. [CODE] EDA — 기본 통계, 결측 처리, 데이터 정제
5. [CODE] EDA 시각화 — 4-panel (매출 추이, 고객 분포, 국가별, 주문 빈도)
6. [MD]  Section 2: 코호트 생성
7. [CODE] 코호트 정의 — 첫 구매 월 기준
8. [CODE] 코호트 피봇 테이블 생성
9. [MD]  Section 3: 리텐션 분석
10. [CODE] 리텐션 히트맵 — seaborn heatmap (핵심 시각화 #1)
11. [CODE] 리텐션 곡선 — 코호트별 라인 차트 (핵심 시각화 #2)
12. [MD]  Section 4: 코호트별 매출 분석
13. [CODE] 코호트별 ARPU(Average Revenue Per User) 추이
14. [CODE] 코호트별 LTV 추정 — 월별 누적 매출 (핵심 시각화 #3)
15. [MD]  Section 5: 세그먼트별 비교
16. [CODE] 국가별(UK vs Non-UK) 리텐션 비교
17. [CODE] 주문 금액 세그먼트별 리텐션 비교
18. [MD]  Section 6: 비즈니스 인사이트
19. [CODE] 정량 요약 — 리텐션율 드랍, LTV 추정, 이탈 위험 구간
20. [MD]  PM에게 전달할 권장사항 + 방법론 한계
```

### 3.3 핵심 시각화 (3개 이상)

| # | 시각화 | 라이브러리 | 용도 |
|---|--------|-----------|------|
| 1 | 코호트 리텐션 히트맵 | seaborn `heatmap` | 월별 리텐션율 패턴 파악 |
| 2 | 리텐션 곡선 (코호트별) | matplotlib `plot` | 코호트 간 리텐션 비교 |
| 3 | 코호트별 누적 LTV | matplotlib `plot` | 매출 기여 장기 추이 |
| 4 | EDA 4-panel | matplotlib `subplots` | 데이터 특성 파악 |

### 3.4 핵심 분석 로직

```python
# 코호트 생성
df['cohort_month'] = df.groupby('CustomerID')['InvoiceDate'].transform('min').dt.to_period('M')
df['order_month'] = df['InvoiceDate'].dt.to_period('M')
df['cohort_index'] = (df['order_month'] - df['cohort_month']).apply(lambda x: x.n)

# 리텐션 테이블
cohort_data = df.groupby(['cohort_month', 'cohort_index'])['CustomerID'].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='cohort_month', columns='cohort_index', values='CustomerID')
cohort_size = cohort_pivot.iloc[:, 0]
retention = cohort_pivot.divide(cohort_size, axis=0)
```

### 3.5 비즈니스 액션 포인트

- Month 1→2 리텐션 드랍 구간 정량화
- 고가치 코호트 vs 저가치 코호트 차이 식별
- 리텐션 개선을 위한 CRM 개입 시점 권장

---

## 4. FR-02: 퍼널 분석 노트북

### 4.1 파일 정보

- **파일명**: `notebooks/case-study-funnel-analysis.ipynb`
- **데이터**: eCommerce Events (cosmetics shop) — `notebooks/cosmetics_events.csv` (1개월 샘플)
- **예상 셀 수**: 18-22 cells

### 4.2 노트북 구조

```
1. [MD]  제목 + 요약 + 분석 구조
2. [CODE] 라이브러리 import + 데이터 로드 (1개월 샘플링)
3. [MD]  Section 1: 탐색적 데이터 분석
4. [CODE] EDA — 이벤트 분포, 유저 수, 카테고리 분포
5. [CODE] EDA 시각화 — 일별 이벤트 추이, 이벤트 타입 비율
6. [MD]  Section 2: 전체 퍼널 분석
7. [CODE] 전체 퍼널 — view → cart → purchase 단계별 유저 수 + 전환율
8. [CODE] 퍼널 바 차트 (핵심 시각화 #1)
9. [MD]  Section 3: 세그먼트별 퍼널 비교
10. [CODE] 카테고리별 퍼널 — 상위 5개 카테고리 비교
11. [CODE] 카테고리별 퍼널 비교 차트 (핵심 시각화 #2)
12. [MD]  Section 4: 이탈 분석
13. [CODE] 단계별 이탈 이유 탐색 — 가격대별 cart→purchase 전환율
14. [CODE] 가격 vs 전환율 산점도 + 추세선 (핵심 시각화 #3)
15. [MD]  Section 5: 시간대별 퍼널 성과
16. [CODE] 요일/시간대별 purchase 전환율 히트맵
17. [MD]  Section 6: 비즈니스 인사이트
18. [CODE] 정량 요약 — 이탈 병목, 매출 기회, ROI 추정
19. [MD]  PM에게 전달할 권장사항 + 방법론 한계
```

### 4.3 핵심 시각화 (3개 이상)

| # | 시각화 | 라이브러리 | 용도 |
|---|--------|-----------|------|
| 1 | 퍼널 바 차트 | matplotlib `barh` | 단계별 전환율과 이탈률 시각화 |
| 2 | 카테고리별 퍼널 비교 | matplotlib grouped bar | 세그먼트 간 병목 차이 |
| 3 | 가격 vs 전환율 | matplotlib `scatter` + 추세선 | 가격 민감도 분석 |
| 4 | 시간대별 전환 히트맵 | seaborn `heatmap` | 시간 패턴 파악 |

### 4.4 핵심 분석 로직

```python
# 퍼널 계산
def calculate_funnel(df):
    viewers = df[df['event_type'] == 'view']['user_id'].nunique()
    carters = df[df['event_type'] == 'cart']['user_id'].nunique()
    purchasers = df[df['event_type'] == 'purchase']['user_id'].nunique()
    return {
        'view': viewers,
        'cart': carters,
        'purchase': purchasers,
        'view_to_cart': carters / viewers if viewers > 0 else 0,
        'cart_to_purchase': purchasers / carters if carters > 0 else 0,
        'overall': purchasers / viewers if viewers > 0 else 0,
    }

# 세그먼트별 퍼널
for category in top_categories:
    cat_df = df[df['category_code'] == category]
    funnel = calculate_funnel(cat_df)
```

### 4.5 비즈니스 액션 포인트

- View→Cart vs Cart→Purchase 중 어디가 더 큰 병목인지 정량화
- 카테고리별 전환율 차이로 마케팅 우선순위 제안
- 가격 민감도를 기반한 프로모션 전략 권장

---

## 5. FR-03: README 리프레이밍

### 5.1 현재 구조 vs 목표 구조

```
현재 README 구조:                    목표 README 구조:
─────────────────                   ─────────────────
1. 프로젝트 소개 (문제 해결)          1. 포트폴리오 헤더 (한 줄 소개)
2. Key Analysis Capabilities        2. 분석 케이스 스터디 갤러리 ★
3. Evidence                         3. 핵심 역량 요약 (분석 관점)
4. Target Users                     4. Key Analysis Capabilities
5. Tech Stack                       5. Evidence (테스트 + 노트북 링크)
6. Features                         6. Tech Stack & Architecture
7. Quickstart                       7. Quickstart
8. Input Data Format                8. API & Data Format
9. API Endpoints                    9. License
10. Tests
11. Deployment
12. License
```

### 5.2 변경 핵심

1. **상단에 "분석 케이스 스터디 갤러리" 섹션 추가** — 노트북별 한 줄 요약 + 핵심 발견 + 시각화 썸네일
2. **"핵심 역량 요약" 추가** — A/B 테스트, SQL, 코호트, 퍼널, 통계를 분석가 관점으로 정리
3. **엔지니어링 세부사항은 하단으로** — 삭제하지 않고 위치만 재배치
4. **Tests, Deployment 등은 간소화** — 접이식(details/summary) 또는 링크로 대체

### 5.3 케이스 스터디 갤러리 형식

```markdown
## Analysis Case Studies

### 1. Marketing A/B Test — HTE Analysis (588K Users)
**데이터**: Kaggle Marketing A/B Testing | **기법**: SRM, z-test, HTE, Dose-response
**핵심 발견**: 광고 노출 50회+ 구간에서 전환 효과 급증 (+5.9%p), 200+회에서 포화
**비즈니스 임팩트**: 증분 매출 $217K, Frequency Cap 적용 시 $137K 추가 잠재
[Notebook](./notebooks/case-study-marketing-ab-test.ipynb) | [SQL Version](./notebooks/case-study-marketing-sql-analysis.ipynb)

### 2. Cohort Retention — E-commerce LTV Analysis
...

### 3. Funnel Analysis — Conversion Bottleneck Detection
...
```

---

## 6. FR-04: 포트폴리오 요약 페이지 (Notion)

### 6.1 Notion 페이지 구조

```
ExperimentOS — Data Analyst Portfolio
├── About Me (간략 소개)
├── Project Overview
│   ├── 문제 정의
│   ├── 해결 방법
│   └── 기술 스택
├── Case Studies
│   ├── 1. Marketing A/B Test (HTE)
│   ├── 2. Cohort Retention
│   ├── 3. Funnel Analysis
│   ├── 4. SRM False Positive Detection
│   └── 5. Sequential Testing Simulation
├── Technical Skills
│   ├── Statistics: SRM, z-test, chi-square, Bayesian, Sequential
│   ├── SQL: DuckDB, CTE, Window Functions, Self-JOIN
│   ├── Python: pandas, numpy, scipy, statsmodels, matplotlib, seaborn
│   └── Engineering: FastAPI, React, TypeScript (부가 역량)
└── Links
    ├── GitHub Repository
    ├── Live Demo
    └── Contact
```

### 6.2 Notion API 활용

MCP `mcp__notion` 또는 `mcp__claude_ai_Notion` 도구를 사용하여 자동 생성:
1. `notion-create-pages`: 메인 포트폴리오 페이지 생성
2. 각 케이스 스터디를 하위 페이지로 생성
3. 시각화 이미지를 노트북에서 추출하여 첨부

---

## 7. 노트북 Convention

기존 4개 노트북의 패턴을 따릅니다:

| 항목 | 규칙 | 예시 |
|------|------|------|
| **파일명** | `case-study-{topic}.ipynb` | `case-study-cohort-retention.ipynb` |
| **첫 번째 셀** | Markdown — 제목 + 요약 + 분석 구조 | 기존 노트북 참고 |
| **두 번째 셀** | Code — import + 데이터 로드 | `sys.path.insert`, `plt.style.use('seaborn-v0_8-whitegrid')` |
| **스타일** | `plt.style.use('seaborn-v0_8-whitegrid')`, figsize (12,5) 기본 | 기존 노트북 동일 |
| **색상** | 기존 팔레트: `#6366f1` (indigo), `#f59e0b` (amber), `#22c55e` (green) | 일관성 유지 |
| **마지막 셀** | Markdown — PM에게 전달할 인사이트 + 방법론 한계 | 기존 노트북 참고 |
| **데이터 파일** | `notebooks/` 디렉토리에 함께 저장 | `notebooks/online_retail.csv` |

---

## 8. Implementation Order

| 순서 | 항목 | 산출물 | 의존성 | 검증 방법 |
|------|------|--------|--------|-----------|
| 1 | 데이터 다운로드 | `notebooks/online_retail.csv`, `notebooks/cosmetics_events.csv` | 없음 | 파일 존재 확인 |
| 2 | FR-01: 코호트 리텐션 노트북 | `notebooks/case-study-cohort-retention.ipynb` | 데이터 | nbconvert 실행 |
| 3 | FR-02: 퍼널 분석 노트북 | `notebooks/case-study-funnel-analysis.ipynb` | 데이터 | nbconvert 실행 |
| 4 | FR-03: README 리프레이밍 | `README.md` 수정 | FR-01, FR-02 | 시각 리뷰 |
| 5 | FR-04: Notion 페이지 | Notion 페이지 URL | FR-03 | 링크 접근 확인 |

---

## 9. Test Plan

### 9.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| 노트북 실행 검증 | 모든 노트북 | `jupyter nbconvert --execute` |
| 기존 테스트 보존 | 209 tests | `python -m pytest tests/ -v` |
| 프론트엔드 빌드 | Vite build | `npm run build` |

### 9.2 Test Cases

- [ ] `case-study-cohort-retention.ipynb` nbconvert 에러 0
- [ ] `case-study-funnel-analysis.ipynb` nbconvert 에러 0
- [ ] 기존 4개 노트북 실행 영향 없음
- [ ] 209 tests 전체 통과
- [ ] README.md 내 모든 링크 유효

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-11 | Initial draft | User |
