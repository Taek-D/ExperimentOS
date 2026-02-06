# ExperimentOS 개선 로드맵
## Antigravity 기반 구현 우선순위

> **목표**: 시장성 극대화 및 실무 도입률 10배 향상  
> **전략**: 마찰 제거 → 핵심 기능 강화 → 엔터프라이즈 전환

---

## 🎯 Phase 1: Quick Wins - 채택률 향상 (0-3개월)

### 1-1. API 연동 기능 추가 ⭐⭐⭐⭐⭐
**우선순위**: CRITICAL - 가장 먼저 구현 필요

#### 구현 내용
- **Statsig API 연동**
  - API Key 입력 UI
  - 실험 ID로 결과 데이터 자동 fetch
  - 실시간 데이터 sync
  
- **GrowthBook API 연동**
  - REST API 클라이언트 구현
  - Experiment metrics 자동 매핑
  
- **Hackle API 연동**
  - SDK 통합
  - 실험 목록 조회 → 선택 → 분석 워크플로우

- **Google Sheets Add-on (보너스)**
  - Apps Script로 ExperimentOS API 호출
  - 스프레드시트에서 버튼 클릭으로 분석 실행

#### 기대 효과
- CSV 업로드 마찰 완전 제거
- 실무 도입 저항 70% 감소
- "실험 도구에서 바로 쓸 수 있다" = 킬러 피처

#### 기술 스택
```python
# Backend (FastAPI)
- httpx for API calls
- OAuth2 for authentication
- Redis for API response caching

# Frontend (React)
- API key management UI
- Experiment selector dropdown
- Auto-sync toggle
```

#### Antigravity 구현 방식
1. `/api/integrations/statsig/experiments` 엔드포인트 생성
2. `IntegrationService` 클래스로 각 플랫폼 추상화
3. Frontend에 "Connect Integration" 버튼 추가

---

### 1-2. Multi-Variant 실험 지원 ⭐⭐⭐⭐⭐
**우선순위**: HIGH - Phase 1에서 필수

#### 구현 내용
- **3개 이상 variant 비교**
  - Control + Treatment1 + Treatment2 + ...
  - Chi-square test for overall significance
  - Pairwise comparison (모든 조합)

- **다중 비교 보정**
  - Bonferroni correction
  - Holm-Bonferroni method
  - False Discovery Rate (FDR) 옵션

- **시각화 개선**
  - Forest plot으로 모든 variant 동시 표시
  - 신뢰구간 겹침 체크

#### CSV 포맷 변경
```csv
variant,users,conversions
control,10000,1200
treatment_A,10000,1350
treatment_B,10000,1280
treatment_C,10000,1400
```

#### 기대 효과
- A/B/C/D 테스트 지원으로 활용 범위 확대
- 복잡한 실험도 분석 가능 → 엔터프라이즈 어필

#### Antigravity 구현 방식
```python
# src/experimentos/analysis.py
def analyze_multivariant(df: pd.DataFrame):
    """n개 variant 동시 분석"""
    # Overall Chi-square test
    # Pairwise z-test with Bonferroni
    # Effect size for each treatment vs control
    pass
```

---

### 1-3. 시각화 강화 ⭐⭐⭐⭐
**우선순위**: HIGH - 사용자 경험 개선

#### 구현 내용
- **Forest Plot (신뢰구간 그래프)**
  - Plotly/Recharts로 interactive 차트
  - Lift ± 95% CI 시각화
  - 통계적 유의성 색상 표시

- **Posterior Distribution (베이지안)**
  - Beta distribution 곡선
  - Credible interval 표시
  - "Treatment가 Control보다 나을 확률: 97%"

- **Power Curve 시각화**
  - 표본 크기 vs 검정력 그래프
  - 현재 표본 크기 마커 표시

- **Guardrail Scorecard**
  - 카드 UI로 모든 가드레일 한눈에
  - 악화/정상 색상 구분 (Red/Yellow/Green)

#### 기술 스택
```typescript
// Frontend
- Recharts (React용 차트 라이브러리)
- D3.js for custom visualizations
- Tailwind CSS for styling
```

#### 기대 효과
- 비전문가도 결과 이해 가능
- "숫자만 보여주는 도구"에서 탈피
- 프레젠테이션에 바로 사용 가능

---

### 1-4. 인터랙티브 튜토리얼 ⭐⭐⭐
**우선순위**: MEDIUM - 온보딩 개선

#### 구현 내용
- **First-time User Experience**
  - 샘플 실험 데이터 자동 로드
  - 단계별 가이드 (Joyride/Shepherd.js)
  - "Try it yourself" 데모 모드

- **Best Practice 가이드**
  - "좋은 실험 설계 5원칙" 문서
  - SRM 해석 방법
  - Decision Memo 읽는 법

- **통계 용어 사전**
  - 마우스 오버 시 설명 툴팁
  - "p-value란?" 같은 간단한 설명

#### Antigravity 구현 방식
```typescript
// TutorialOverlay.tsx
import Joyride from 'react-joyride';

const steps = [
  { target: '.upload-area', content: '여기서 CSV 업로드' },
  { target: '.health-check', content: 'SRM 자동 체크' },
  // ...
];
```

#### 기대 효과
- 신규 유저 이탈률 50% 감소
- 지원 요청 감소
- 입소문 확산 ("쓰기 진짜 쉽다")

---

## 🚀 Phase 2: 핵심 차별화 - 기능 고도화 (3-6개월)

### 2-1. Sequential Testing (조기 종료) ⭐⭐⭐⭐⭐
**우선순위**: CRITICAL - 실무 필수 기능

#### 구현 내용
- **Alpha Spending Function**
  - O'Brien-Fleming boundary
  - Pocock boundary
  - Haybittle-Peto boundary

- **Sequential Confidence Intervals**
  - 현재 look에서의 adjusted CI
  - "지금 멈춰도 Type I Error < 5%"

- **실시간 모니터링 UI**
  - 실험 진행률 표시
  - "지금 종료 가능" / "더 기다려야 함" 배지
  - 예상 종료일 계산

#### 이론적 배경
```
O'Brien-Fleming:
- 초반에는 엄격한 기준 (z > 4.0)
- 후반에는 완화 (z > 1.96)
- 실무에서 가장 많이 사용
```

#### 기대 효과
- 실험 기간 평균 30% 단축
- 조기 성공/실패 탐지 → 리소스 절약
- 경쟁사 대비 핵심 차별화 포인트

#### Antigravity 구현 방식
```python
# src/experimentos/sequential.py
from scipy.stats import norm

def obrien_fleming_boundary(looks: int, alpha: float = 0.05):
    """OF boundary 계산"""
    # Lan-DeMets alpha spending
    pass

def check_early_stop(current_look: int, z_stat: float):
    """조기 종료 가능 여부"""
    pass
```

---

### 2-2. Segmentation Analysis ⭐⭐⭐⭐
**우선순위**: HIGH - 인사이트 깊이 향상

#### 구현 내용
- **세그먼트별 효과 분석**
  - CSV에 `segment` 컬럼 추가 (country, platform 등)
  - 각 세그먼트별 lift 계산
  - Interaction effect 탐지

- **자동 HTE 탐지**
  - "모바일에서만 효과 있음" 자동 발견
  - "신규 유저 vs 기존 유저" 효과 차이

- **Subgroup Tree 분석**
  - Decision tree로 "어떤 조합에서 효과 큰가" 탐색
  - Causal forest (고급 옵션)

#### CSV 포맷 예시
```csv
variant,users,conversions,country,platform,user_type
control,5000,600,KR,mobile,new
treatment,5000,700,KR,mobile,new
control,3000,400,KR,desktop,existing
treatment,3000,420,KR,desktop,existing
```

#### 기대 효과
- "전체적으로는 효과 없지만 특정 세그먼트에서 유의" 발견
- 타겟 롤아웃 전략 수립 가능
- 분석 깊이 10배 향상

---

### 2-3. 실험 히스토리 & DB 저장 ⭐⭐⭐⭐
**우선순위**: HIGH - B2B 전환 필수

#### 구현 내용
- **PostgreSQL/MySQL 연동**
  - 실험 메타데이터 저장 (ID, 이름, 날짜, 담당자)
  - 분석 결과 저장 (lift, CI, p-value)
  - Decision Memo 히스토리

- **실험 목록 페이지**
  - 진행 중 / 완료 / 롤백 필터
  - 검색 기능 (실험명, 담당자)
  - 정렬 (날짜, 상태)

- **실험 상세 페이지**
  - 과거 분석 결과 조회
  - 버전 관리 (재분석 시 히스토리)

#### DB Schema
```sql
CREATE TABLE experiments (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  owner VARCHAR(100),
  status VARCHAR(20), -- running/completed/rollback
  created_at TIMESTAMP,
  primary_metric VARCHAR(100),
  decision VARCHAR(20) -- launch/hold/rollback
);

CREATE TABLE analysis_results (
  id UUID PRIMARY KEY,
  experiment_id UUID REFERENCES experiments(id),
  analyzed_at TIMESTAMP,
  lift_absolute FLOAT,
  lift_relative FLOAT,
  p_value FLOAT,
  decision_memo TEXT
);
```

#### 기대 효과
- 조직 차원의 실험 관리 가능
- "이전에 비슷한 실험 했는데..." 검색 가능
- 엔터프라이즈 필수 요구사항 충족

---

### 2-4. 팀 협업 기능 ⭐⭐⭐⭐
**우선순위**: MEDIUM-HIGH - 조직 도입 촉진

#### 구현 내용
- **댓글/리뷰 시스템**
  - 실험 결과에 코멘트 달기
  - @mention으로 담당자 태그
  - 이메일 알림

- **승인 워크플로우**
  - PM이 "Approve" 버튼 클릭 후 배포 가능
  - 승인 히스토리 추적

- **권한 관리**
  - Viewer / Analyst / Admin 역할
  - Organization 단위 멤버 관리

#### 기술 스택
```typescript
// Backend
- PostgreSQL for comments/approvals
- WebSocket for real-time notifications

// Frontend
- Comment component with @mention
- Approval button with confirmation modal
```

#### 기대 효과
- 이메일/Slack 왔다갔다 제거
- 의사결정 프로세스 투명화
- 팀 단위 구독 전환 가능

---

## 💎 Phase 3: 엔터프라이즈 & AI - 시장 지배력 (6-12개월)

### 3-1. AI-Powered Insights ⭐⭐⭐⭐⭐
**우선순위**: VERY HIGH - 차세대 기능

#### 구현 내용
- **LLM 기반 Decision Memo 생성**
  - GPT-4로 "Next Actions" 자동 작성
  - "과거 유사 실험 패턴" 검색 후 인사이트
  - "이상 패턴 탐지" (트래픽 급증일 체크)

- **자연어 질의**
  - "모바일 유저에서 효과 있었나요?"
  - "가드레일 악화 원인이 뭘까요?"

- **실험 추천 시스템**
  - "이 실험 결과가 Hold면, 다음에 시도할 만한 변형은..."

#### 프롬프트 예시
```
당신은 실험 분석 전문가입니다.

실험 결과:
- Primary Metric: Conversion Rate
- Lift: +2.3% (95% CI: [0.8%, 3.8%])
- p-value: 0.003
- Guardrail: Cancel Rate +0.2%p (worsened)

결정: HOLD

다음 액션을 제안하세요:
1. 왜 Hold인지 근거
2. Guardrail 악화 원인 가설 3가지
3. 다음 시도할 실험 아이디어 2가지
```

#### 기대 효과
- Decision Memo 작성 시간 90% 단축
- 주니어 분석가도 시니어 수준 메모 작성
- "AI 실험 코파일럿" 브랜딩 가능

#### Antigravity 구현 방식
```python
# backend/llm_service.py
import openai

async def generate_next_actions(experiment_data: dict) -> str:
    """GPT-4로 Next Actions 생성"""
    prompt = f"""
    실험 결과:
    {experiment_data}
    
    다음 액션 제안:
    """
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

---

### 3-2. ROI & Business Impact Calculator ⭐⭐⭐⭐
**우선순위**: HIGH - 경영진 설득 도구

#### 구현 내용
- **ROI 계산기**
  - Lift × 전체 트래픽 × 단위 매출
  - "연간 예상 매출 증가: 5억원"

- **Cost-Benefit Analysis**
  - 개발 비용 입력 UI
  - Payback period 계산
  - NPV (순현재가치) 산출

- **Long-term Projection**
  - Novelty effect 감쇠율 반영
  - 3개월 / 6개월 / 1년 후 예상 효과

#### UI 예시
```
💰 비즈니스 임팩트 요약

전체 롤아웃 시:
- 월간 추가 전환: +15,000건
- 월간 추가 매출: ₩450,000,000
- 연간 예상 매출: ₩5,400,000,000

개발 비용: ₩100,000,000
투자 회수 기간: 0.7개월

✅ ROI: 5,300% (1년 기준)
```

#### 기대 효과
- 실험 가치를 경영진 언어로 번역
- 우선순위 결정 시 객관적 지표 제공
- 스타트업 → 엔터프라이즈 확장 시 필수

---

### 3-3. Slack 봇 통합 ⭐⭐⭐⭐
**우선순위**: HIGH - 워크플로우 혁신

#### 구현 내용
- **Slash Command**
  - `/experimentos analyze EXP-123`
  - 실험 ID 입력하면 자동 분석 후 결과 포스팅

- **Interactive Message**
  - 분석 완료 시 채널에 Decision Memo 요약
  - "Approve" / "Request Changes" 버튼
  - 스레드에서 토론 가능

- **Daily Digest**
  - 매일 오전 9시 "진행 중 실험 요약" 자동 발송
  - "Sample Size 충분한 실험" 알림

#### 기술 스택
```python
# Slack Bolt framework
from slack_bolt.async_app import AsyncApp

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

@app.command("/experimentos")
async def analyze_experiment(ack, command, say):
    await ack()
    exp_id = command['text']
    # API 호출 후 결과 포스팅
    await say(f"분석 중... {exp_id}")
```

#### 기대 효과
- 분석가가 Slack 떠날 필요 없음
- 실시간 협업 활성화
- 바이럴 확산 ("우리 팀도 써보자")

---

### 3-4. 모바일 앱 ⭐⭐⭐
**우선순위**: MEDIUM - 접근성 향상

#### 구현 내용
- **React Native 앱**
  - 실험 목록 조회
  - Decision Memo 읽기 (읽기 전용)
  - Push 알림 (실험 완료 시)

- **Progressive Web App (PWA)**
  - 오프라인 지원
  - 홈 화면에 추가 가능

#### 기대 효과
- 이동 중에도 결과 확인
- PM/임원이 출장 중에도 승인 가능

---

## 🔧 Technical Debt & Infrastructure

### 보안 & 컴플라이언스
- [ ] 데이터 암호화 (AES-256)
- [ ] HTTPS 강제
- [ ] Rate limiting
- [ ] GDPR 준수 (데이터 삭제 요청)
- [ ] SSO/SAML 지원 (Okta, Azure AD)

### 성능 최적화
- [ ] Redis 캐싱 (API 응답)
- [ ] PostgreSQL 인덱싱
- [ ] CDN for static assets
- [ ] Render → AWS/GCP 마이그레이션 (슬립 모드 제거)

### 테스트 & 모니터링
- [ ] E2E 테스트 (Playwright)
- [ ] Sentry for error tracking
- [ ] Mixpanel/Amplitude for analytics
- [ ] Uptime monitoring (UptimeRobot)

---

## 💰 Freemium 모델 설계

### Free Tier
- 월 10개 실험 분석
- CSV 업로드만 지원
- 기본 Decision Memo
- 커뮤니티 지원

### Pro Tier ($99/month)
- Unlimited 실험
- API 연동 (Statsig, GrowthBook)
- Sequential Testing
- 고급 시각화
- 이메일 지원

### Enterprise Tier (Custom Pricing)
- 모든 Pro 기능
- 팀 협업 (댓글, 승인)
- SSO/SAML
- SLA 보장
- 전담 Customer Success Manager
- On-premise 배포 옵션

---

## 📊 성공 지표 (KPIs)

### Phase 1
- [ ] 주간 활성 사용자(WAU) 100명
- [ ] API 연동 사용률 30%
- [ ] 평균 세션 시간 10분 이상

### Phase 2
- [ ] 유료 전환율 5%
- [ ] 팀 단위 가입 20개 조직
- [ ] NPS 점수 50+ (promoter 비율)

### Phase 3
- [ ] MRR $10,000
- [ ] Enterprise 고객 5개사
- [ ] Churn Rate < 5%

---

## 🚦 구현 우선순위 요약

### 🔴 Must Have (Phase 1 - 3개월)
1. API 연동 (Statsig, GrowthBook, Hackle)
2. Multi-variant 지원
3. 시각화 강화 (Forest Plot, CI 그래프)
4. 튜토리얼 & 온보딩

### 🟡 Should Have (Phase 2 - 6개월)
5. Sequential Testing
6. Segmentation Analysis
7. 실험 히스토리 DB
8. 팀 협업 기능

### 🟢 Nice to Have (Phase 3 - 12개월)
9. AI-Powered Insights
10. ROI Calculator
11. Slack 봇
12. 모바일 앱

---

## 🎯 Next Steps

1. **Week 1-2**: API 연동 프로토타입 (Statsig 우선)
2. **Week 3-4**: Multi-variant 로직 구현 + 테스트
3. **Week 5-6**: 시각화 컴포넌트 개발
4. **Week 7-8**: 베타 테스터 모집 (3개 회사)
5. **Week 9-12**: 피드백 반영 + 정식 런칭

---

## 📚 참고 자료

### 경쟁사 분석
- Statsig: Sequential Testing, Pulse Results
- Eppo: Causal inference, metric definitions
- Optimizely: Multi-armed bandit, personalization

### 학술 자료
- Kohavi et al., "Trustworthy Online Controlled Experiments"
- Johari et al., "Peeking at A/B Tests"
- Deng et al., "Improving the Sensitivity of Online Controlled Experiments"

### 오픈소스
- GrowthBook (MIT License) - 참고할 만한 구조
- Apache Superset - 시각화 아이디어

---

**문서 버전**: v1.0  
**최종 수정**: 2026-02-03  
**작성자**: ExperimentOS Team
