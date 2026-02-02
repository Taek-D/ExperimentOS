"""간단한 healthcheck 모듈 테스트"""
import sys
sys.path.insert(0, 'e:/프로젝트/안티그래비티 프로젝트/에이블리')

import pandas as pd
from src.experimentos.healthcheck import validate_schema, detect_srm

# 테스트 1: 정상 데이터
print("테스트 1: 정상 데이터")
df = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [1200, 1320]
})
result = validate_schema(df)
print(f"  결과: {result['status']}")
assert result["status"] == "Healthy", f"Expected Healthy, got {result['status']}"
print("  ✅ 통과")

# 테스트 2: conversions > users
print("\n테스트 2: conversions > users")
df = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [12000, 1320]
})
result = validate_schema(df)
print(f"  결과: {result['status']}")
assert result["status"] == "Blocked", f"Expected Blocked, got {result['status']}"
print("  ✅ 통과")

# 테스트 3: SRM 정상
print("\n테스트 3: SRM 정상 (50/50)")
result = detect_srm(10000, 10000, (50, 50))
print(f"  결과: {result['status']}, p-value: {result['p_value']:.6f}")
assert result["status"] == "Healthy", f"Expected Healthy, got {result['status']}"
print("  ✅ 통과")

# 테스트 4: SRM 경고
print("\n테스트 4: SRM 경고")
result = detect_srm(5000, 7000, (50, 50))
print(f"  결과: {result['status']}, p-value: {result['p_value']:.6f}")
assert result["status"] in ["Warning", "Blocked"], f"Expected Warning/Blocked, got {result['status']}"
print("  ✅ 통과")

print("\n🎉 모든 기본 테스트 통과!")
