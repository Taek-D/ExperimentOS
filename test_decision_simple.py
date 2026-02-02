"""간단한 decision 테스트"""
import sys
sys.path.insert(0, 'e:/프로젝트/안티그래비티 프로젝트/에이블리')

from src.experimentos.memo import make_decision

# 테스트 1: Launch (Primary 유의 + Guardrail 정상)
print("테스트 1: Launch (Primary 유의 + Guardrail 정상)")
health = {
    "overall_status": "Healthy",
    "schema": {"status": "Healthy", "issues": []},
    "srm": {"status": "Healthy", "p_value": 0.9}
}
primary = {
    "is_significant": True,
    "p_value": 0.001,
    "absolute_lift": 0.02,
    "relative_lift": 0.2,
    "ci_95": [0.01, 0.03]
}
guardrails = []

result = make_decision(health, primary, guardrails)
print(f"  Decision: {result['decision']}")
print(f"  Reason: {result['reason']}")
assert result["decision"] == "Launch"
print("  ✅ 통과")

# 테스트 2: Hold (Primary 비유의)
print("\n테스트 2: Hold (Primary 비유의)")
health = {
    "overall_status": "Healthy",
    "schema": {"status": "Healthy", "issues": []},
    "srm": {"status": "Healthy", "p_value": 0.9}
}
primary = {"is_significant": False, "p_value": 0.3, "absolute_lift": 0.001}
guardrails = []

result = make_decision(health, primary, guardrails)
print(f"  Decision: {result['decision']}")
print(f"  Reason: {result['reason']}")
assert result["decision"] == "Hold"
print("  ✅ 통과")

# 테스트 3: Rollback (Severe Guardrail)
print("\n테스트 3: Rollback (Severe Guardrail)")
health = {
    "overall_status": "Healthy",
    "schema": {"status": "Healthy", "issues": []},
    "srm": {"status": "Healthy", "p_value": 0.9}
}
primary = {"is_significant": True, "p_value": 0.001, "absolute_lift": 0.02, "relative_lift": 0.2, "ci_95": [0.01, 0.03]}
guardrails = [
    {"name": "error_rate", "delta": 0.004, "worsened": True, "severe": True}
]

result = make_decision(health, primary, guardrails)
print(f"  Decision: {result['decision']}")
print(f"  Reason: {result['reason']}")
assert result["decision"] == "Rollback"
print("  ✅ 통과")

print("\n🎉 모든 Decision 테스트 통과!")
