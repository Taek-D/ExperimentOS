# Design Rationale: Statistical Thresholds

> ExperimentOS의 `config.py`에 정의된 각 임계값의 선택 근거를 설명합니다.
> 모든 임계값은 학술 문헌, 업계 표준, 또는 수학적 추론에 기반합니다.

---

## 1. SRM Detection Thresholds

### SRM_WARNING_THRESHOLD = 0.001

| 항목 | 내용 |
|------|------|
| **의미** | Chi-square 검정 p-value < 0.001이면 SRM Warning |
| **근거** | Microsoft ExP 플랫폼 기준 (Fabijan et al., KDD 2019) |
| **왜 0.05가 아닌가** | SRM은 **실험 자체의 타당성(internal validity)**을 판단합니다. 효과 크기의 유의성 판단(α=0.05)과는 다른 맥락입니다. 0.05를 사용하면 정상 실험의 ~5%에서 False Alarm이 발생하여 분석 파이프라인에 과도한 노이즈를 생성합니다. |
| **왜 0.001인가** | 50/50 배정에서 p < 0.001은 10만 유저 기준 약 300명 이상의 불균형에 해당합니다. 이 수준의 차이는 무작위 변동으로 설명하기 어렵고, 기술적 버그나 봇 트래픽 등 체계적 원인을 의심해야 합니다. |
| **참고 문헌** | Fabijan, A. et al. "Diagnosing Sample Ratio Mismatch in Online Controlled Experiments." KDD 2019. |

### SRM_BLOCKED_THRESHOLD = 0.00001

| 항목 | 내용 |
|------|------|
| **의미** | p < 0.00001이면 실험 자동 차단 (Blocked) |
| **근거** | 5σ 수준. 입자물리학의 "발견" 기준과 유사한 확실성 |
| **왜 이 값인가** | 이 수준의 p-value는 우연으로 설명할 수 없습니다. 10만 번 실험해도 1회 미만으로 발생할 확률이므로, 체계적 문제가 확실하다고 판단합니다. Warning과 Blocked의 2단계 구조는 분석가가 Warning 단계에서 원인을 조사할 여유를 제공하면서, Blocked에서는 자동으로 의사결정을 중단합니다. |
| **대안 검토** | Optimizely는 p < 0.01, VWO는 p < 0.005를 사용합니다. ExperimentOS는 더 보수적인 접근을 선택하여, 불필요한 차단을 줄이되 위험한 실험이 통과하지 못하게 합니다. |

---

## 2. Guardrail Degradation Thresholds

### GUARDRAIL_WORSENED_THRESHOLD = 0.001 (0.1%p)

| 항목 | 내용 |
|------|------|
| **의미** | Treatment의 guardrail 지표가 Control 대비 0.1%p 이상 악화되면 Warning |
| **근거** | 업계 관행 + 비즈니스 민감도 분석 |
| **왜 이 값인가** | 0.1%p는 기저율(base rate)이 낮은 지표(오류율 ~0.5%, 취소율 ~1%)에서 **상대적으로 10-20% 악화**에 해당합니다. 이 수준은 통계적 노이즈일 수도 있지만, 모니터링 대상으로 표시하기에 적절합니다. |
| **절대값 vs 상대값** | 절대값(Δ)을 사용하는 이유: 기저율이 매우 낮은 지표(예: 크래시율 0.01%)에서 상대 변화율은 민감하지만, 비즈니스 영향은 미미합니다. 절대값이 실제 사용자 경험에 미치는 영향을 더 직관적으로 반영합니다. |

### GUARDRAIL_SEVERE_THRESHOLD = 0.003 (0.3%p)

| 항목 | 내용 |
|------|------|
| **의미** | 0.3%p 이상 악화되면 Severe (의사결정에 직접 영향) |
| **근거** | Worsened 임계값의 3배. Microsoft/Booking.com 사례 참고 |
| **왜 이 값인가** | Worsened와 Severe의 비율(1:3)은 업계 관행에서 흔한 패턴입니다. 기저율 1%인 지표에서 0.3%p 악화는 상대적으로 30% 증가를 의미하며, 이는 비즈니스적으로 무시할 수 없는 수준입니다. |
| **Decision에 미치는 영향** | Severe guardrail은 primary metric이 유의하더라도 Launch를 차단합니다. 이는 "국소 최적화(local optimization)"를 방지하는 설계 원칙입니다. 전환율이 올라도 오류율이 급증하면 순 가치는 음수일 수 있습니다. |
| **참고** | Kohavi et al. (2020) Ch. 8 "Guardrails: Protecting against Regressions" |

---

## 3. Statistical Settings

### SIGNIFICANCE_ALPHA = 0.05

| 항목 | 내용 |
|------|------|
| **의미** | Type I Error Rate (False Positive Rate) = 5% |
| **근거** | Fisher (1925) 이래 사회과학/산업계 표준 |
| **왜 0.01이 아닌가** | 0.01은 의학/규제 환경에서 적절하지만, A/B 테스트에서는 Type II Error(효과를 놓침)의 비용이 Type I Error(잘못된 출시)의 비용보다 높은 경우가 많습니다. α=0.01로 낮추면 필요 표본이 ~50% 증가하여 실험 기간이 길어집니다. |
| **왜 0.10이 아닌가** | 0.10은 탐색적 분석에서 허용되지만, 의사결정 도구에서는 너무 관대합니다. 10번 중 1번 거짓 양성이 발생하면 조직의 실험 문화에 대한 신뢰를 훼손합니다. |
| **조정 가능성** | `ExperimentConfig`를 인스턴스화할 때 override 가능합니다. Multi-variant에서는 Bonferroni 보정이 자동 적용되어 Family-Wise Error Rate를 유지합니다. |

### MULTIPLE_TESTING_METHOD = "bonferroni"

| 항목 | 내용 |
|------|------|
| **의미** | Multi-variant 테스트에서 p-value 보정 방법 |
| **근거** | Bonferroni는 가장 보수적이고 가장 이해하기 쉬운 보정법 |
| **왜 Bonferroni인가** | ExperimentOS의 타겟 사용자(PM, 분석가)에게 **설명 가능성**이 중요합니다. "p-value에 비교 횟수를 곱한다"는 직관적 설명이 가능합니다. |
| **Holm과의 비교** | Holm step-down은 Bonferroni보다 검정력이 높지만, 보정 후 p-value가 순서에 의존하여 비전문가에게 혼란을 줍니다. 대안으로 제공(`holm`, `fdr_bh` 선택 가능)하되 기본값은 Bonferroni입니다. |
| **FDR_BH** | Benjamini-Hochberg FDR은 많은 비교(>10)에 적합하지만, A/B 테스트의 variant 수는 보통 3-5개이므로 FWER 제어가 더 적절합니다. |
| **참고** | Hochberg, Y. & Tamhane, A. (1987). *Multiple Comparison Procedures*. Wiley. |

---

## 4. Sample Quality Settings

### MIN_SAMPLE_SIZE_WARNING = 100

| 항목 | 내용 |
|------|------|
| **의미** | variant당 100명 미만이면 소표본 경고 |
| **근거** | 정규 근사(normal approximation)의 적용 가능 조건 |
| **왜 이 값인가** | Z-test와 chi-square 검정은 정규 근사에 기반합니다. `np >= 5` 규칙(n: 표본 수, p: 전환율)에서, 전환율 5%일 때 n=100이면 np=5로 최소 조건을 만족합니다. 더 낮은 전환율에서는 더 큰 표본이 필요하지만, 100은 "분석 결과를 보여줘도 되는 최소 기준"으로 설정했습니다. |
| **행동** | Warning만 표시하고 분석은 진행합니다. 소표본에서 p-value 자체가 유의하기 어려우므로, 잘못된 결정으로 이어질 가능성은 낮습니다(보수적 실패). |

---

## 5. Bayesian Settings

### BAYES_SAMPLES = 10,000

| 항목 | 내용 |
|------|------|
| **의미** | Monte Carlo 시뮬레이션 샘플 수 |
| **근거** | 정밀도-성능 트레이드오프 |
| **왜 이 값인가** | Beta 분포의 Monte Carlo 추정에서 10,000 샘플은 "Treatment이 더 나을 확률"의 표준 오차를 ~0.5%p 이내로 제한합니다 (SE ≈ 1/√n ≈ 0.01). API 응답 시간(< 500ms)과 정밀도의 균형점입니다. |
| **왜 100,000이 아닌가** | 10배 증가 시 SE는 ~0.16%p로 개선되지만, Render Free Tier의 메모리/CPU 제약과 응답 시간 목표(< 1초)를 고려하면 과도합니다. 결과는 의사결정 참고용이지 규제 보고용이 아닙니다. |
| **베이지안 결과의 역할** | ExperimentOS에서 베이지안 분석은 **설명용**입니다. 의사결정(make_decision)은 빈도론적 분석(z-test + guardrails)에만 의존합니다. 따라서 베이지안 추정의 정밀도 요구는 상대적으로 낮습니다. |

### BAYES_SEED = 42

| 항목 | 내용 |
|------|------|
| **의미** | 난수 시드 고정 |
| **근거** | 재현성(Reproducibility) |
| **왜 42인가** | 관례적 값. 같은 입력 데이터에 대해 항상 같은 결과를 반환하여, 테스트 가능성과 디버깅 용이성을 보장합니다. |

---

## 6. Sequential Testing Settings

### SEQUENTIAL_MAX_LOOKS = 5

| 항목 | 내용 |
|------|------|
| **의미** | 기본 최대 중간 분석(interim analysis) 횟수 |
| **근거** | FDA 임상시험 가이드라인 및 Jennison & Turnbull (1999) |
| **왜 5인가** | 중간 분석 횟수가 늘어나면 alpha spending이 분산되어 각 look의 경계값이 높아지고, 검정력이 떨어집니다. 실무적으로 2주 실험에서 매일 분석하는 것보다, 주요 마일스톤(20%/40%/60%/80%/100% 데이터 수집)에서 분석하는 것이 효율적입니다. 5회는 이 패턴과 일치합니다. |
| **1-2회 vs 5회** | 1-2회는 조기 종료 기회가 너무 적어 sequential testing의 이점이 줄어듭니다. |
| **10회 이상** | O'Brien-Fleming spending에서 10+ looks는 첫 번째 look의 boundary가 매우 높아져 (z > 4.0+), 실질적으로 조기 종료가 불가능합니다. |
| **참고** | Jennison, C. & Turnbull, B.W. (1999). *Group Sequential Methods with Applications to Clinical Trials*. Chapman & Hall/CRC. |

### SEQUENTIAL_BOUNDARY_TYPE = "obrien_fleming"

| 항목 | 내용 |
|------|------|
| **의미** | Alpha spending function 유형 |
| **근거** | 업계 표준 + 보수적 특성 |
| **OBF vs Pocock** | O'Brien-Fleming은 초기에 매우 높은 boundary를 설정하고 후반에 완화합니다. 이는 "충분한 데이터 없이 조기 종료"하는 위험을 최소화합니다. Pocock은 모든 look에서 동일한 boundary를 사용하여 조기 종료가 더 쉽지만, 최종 분석의 α가 줄어듭니다. |
| **기본값으로 OBF를 선택한 이유** | A/B 테스트에서 "너무 일찍 종료"하는 비용(잘못된 결론)이 "조금 더 기다리는" 비용(추가 실험 기간)보다 큽니다. OBF는 이 비대칭성을 반영합니다. |
| **참고** | O'Brien, P.C. & Fleming, T.R. (1979). "A Multiple Testing Procedure for Clinical Trials." *Biometrics*, 35(3), 549-556. |

---

## 7. Design Principle: Conservative Defaults

ExperimentOS의 모든 기본값은 **보수적(conservative)** 방향으로 설정되어 있습니다:

| 원칙 | 적용 |
|------|------|
| **Type I Error 최소화** | SRM threshold가 0.05가 아닌 0.001 |
| **FWER 제어** | FDR이 아닌 Bonferroni |
| **조기 종료 신중** | Pocock이 아닌 O'Brien-Fleming |
| **Guardrail 보호** | Primary가 유의해도 severe guardrail이면 차단 |

이는 "잘못된 Launch를 방지하는 것"이 "좋은 실험을 놓치는 것"보다 비즈니스적으로 중요하다는 판단에 기반합니다.

잘못된 Launch → 사용자 경험 악화 → 매출 하락 + 롤백 비용 + 신뢰 손상
좋은 실험을 놓침 → 추가 실험 기간 → 비용은 있지만 위험은 없음

---

## References

1. Fabijan, A. et al. (2019). "Diagnosing Sample Ratio Mismatch in Online Controlled Experiments." *KDD 2019*.
2. Kohavi, R., Tang, D., & Xu, Y. (2020). *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing*. Cambridge University Press.
3. Fisher, R.A. (1925). *Statistical Methods for Research Workers*. Oliver & Boyd.
4. Hochberg, Y. & Tamhane, A. (1987). *Multiple Comparison Procedures*. Wiley.
5. Jennison, C. & Turnbull, B.W. (1999). *Group Sequential Methods with Applications to Clinical Trials*. Chapman & Hall/CRC.
6. O'Brien, P.C. & Fleming, T.R. (1979). "A Multiple Testing Procedure for Clinical Trials." *Biometrics*, 35(3), 549-556.
7. Benjamini, Y. & Hochberg, Y. (1995). "Controlling the False Discovery Rate." *JRSS-B*, 57(1), 289-300.

---

*문서 버전: v1.0*
*최종 수정: 2026-02-10*
