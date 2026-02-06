"""
실험 분석 설정 (Configuration)

모든 threshold와 기본값을 중앙화하여 관리합니다.
기본값은 PRD 및 README의 기준을 따릅니다.
"""

from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    """
    실험 분석 설정
    
    모든 threshold와 기본값을 한 곳에서 관리합니다.
    기본값은 PRD 문서 기준입니다.
    """
    
    # ===== SRM Detection Thresholds =====
    SRM_WARNING_THRESHOLD: float = 0.001
    """SRM Warning 임계값 (p < 0.001 → Warning)"""
    
    SRM_BLOCKED_THRESHOLD: float = 0.00001
    """SRM Blocked 임계값 (p < 0.00001 → Blocked)"""
    
    # ===== Guardrail Degradation Thresholds =====
    GUARDRAIL_WORSENED_THRESHOLD: float = 0.001
    """Guardrail Worsened 임계값 (Δ >= 0.1%p = 0.001)"""
    
    GUARDRAIL_SEVERE_THRESHOLD: float = 0.003
    """Guardrail Severe 임계값 (Δ >= 0.3%p = 0.003)"""
    
    # ===== Traffic Split =====
    DEFAULT_EXPECTED_SPLIT: tuple[float, float] = (50.0, 50.0)
    """기본 트래픽 분배 비율 (Control%, Treatment%)"""
    
    # ===== Statistical Settings =====
    SIGNIFICANCE_ALPHA: float = 0.05
    """유의수준 (α = 0.05, 95% CI)"""
    
    # ===== Small Sample Warning =====
    MIN_SAMPLE_SIZE_WARNING: int = 100
    """작은 표본 경고 기준 (users < 100 → Warning)"""
    
    # ===== Multi-variant Settings =====
    MULTIPLE_TESTING_METHOD: str = "bonferroni"
    """다중 비교 보정 방법 (bonferroni, holm, fdr_bh, none)"""

    # ===== Continuous & Bayesian Settings (V1) =====
    VAR_TOLERANCE: float = 1e-9
    """분산 계산 시 부동소수점 오차 허용 범위"""
    
    BAYES_SAMPLES: int = 10000
    """베이지안 시뮬레이션 샘플 수"""
    
    BAYES_SEED: int = 42
    """베이지안 시뮬레이션 난수 시드 (Deterministic)"""

    # ===== UI Configuration =====
    HYPOTHESIS_TEXT_AREA_HEIGHT: int = 100
    """가설 입력 텍스트 영역 높이 (px)"""

    def get_assumptions_text(self) -> str:
        """
        Memo에 포함할 Assumptions & Thresholds 텍스트 생성
        
        Returns:
            str: Markdown 형식 assumptions 섹션
        """
        return f"""---

## 📋 Assumptions & Thresholds

**Statistical Settings:**
- Significance Level: α = {self.SIGNIFICANCE_ALPHA} (95% Confidence Interval)
- Expected Traffic Split: {self.DEFAULT_EXPECTED_SPLIT[0]:.0f}% / {self.DEFAULT_EXPECTED_SPLIT[1]:.0f}%

**SRM (Sample Ratio Mismatch) Detection:**
- ⚠️ Warning: p < {self.SRM_WARNING_THRESHOLD}
- 🚫 Blocked: p < {self.SRM_BLOCKED_THRESHOLD}

**Guardrail Degradation:**
- ⚠️ Worsened: Δ ≥ {self.GUARDRAIL_WORSENED_THRESHOLD * 100:.1f}%p ({self.GUARDRAIL_WORSENED_THRESHOLD})
- 🚫 Severe: Δ ≥ {self.GUARDRAIL_SEVERE_THRESHOLD * 100:.1f}%p ({self.GUARDRAIL_SEVERE_THRESHOLD})

**Quality Checks:**
- Small Sample Warning: users < {self.MIN_SAMPLE_SIZE_WARNING}
"""


# Singleton instance
config = ExperimentConfig()
"""전역 설정 인스턴스 (기본값 사용)"""


# Convenience accessors (backward compatibility)
SRM_WARNING_THRESHOLD = config.SRM_WARNING_THRESHOLD
SRM_BLOCKED_THRESHOLD = config.SRM_BLOCKED_THRESHOLD
GUARDRAIL_WORSENED_THRESHOLD = config.GUARDRAIL_WORSENED_THRESHOLD
GUARDRAIL_SEVERE_THRESHOLD = config.GUARDRAIL_SEVERE_THRESHOLD
DEFAULT_EXPECTED_SPLIT = config.DEFAULT_EXPECTED_SPLIT
SIGNIFICANCE_ALPHA = config.SIGNIFICANCE_ALPHA
MIN_SAMPLE_SIZE_WARNING = config.MIN_SAMPLE_SIZE_WARNING
MULTIPLE_TESTING_METHOD = config.MULTIPLE_TESTING_METHOD
