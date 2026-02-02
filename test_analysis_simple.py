"""간단한 analysis 모듈 테스트 (상세 디버깅)"""
import sys
sys.path.insert(0, 'e:/프로젝트/안티그래비티 프로젝트/에이블리')

import pandas as pd
from src.experimentos.analysis import calculate_primary

# 테스트 1: 유의한 차이 (10% vs 12%, N=10000)
print("테스트 1: 유의한 차이 (10% vs 12%)")
df = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [1000, 1200]
})
result = calculate_primary(df)
print(f"  Lift: {result['absolute_lift']:.4f} ({result['relative_lift']:.1%})")
print(f"  P-value: {result['p_value']}")  # 생략 없이 출력
print(f"  Is Significant: {result['is_significant']}")
print(f"  CI: {result['ci_95']}")

if result["is_significant"]:
    print("  ✅ 통과 (유의함)")
else:
    print("  ❌ 실패 (유의하지 않음으로 판정됨)")

print("\n---")

# 테스트 2: p-value 직접 계산 (scipy 사용)
from scipy import stats
users_c = 10000
conv_c = 1000
users_t = 10000
conv_t = 1200

# Chi2 test로 교차 검증
obs = [[conv_c, users_c - conv_c], [conv_t, users_t - conv_t]]
chi2, p, dof, ex = stats.chi2_contingency(obs)
print(f"Scipy Chi2 P-value: {p}")
