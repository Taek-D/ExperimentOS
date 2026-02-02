"""
Sample CSV Generator

빠른 데모를 위한 샘플 CSV 파일들을 생성합니다.
"""

import pandas as pd
import os

# 출력 디렉토리
OUTPUT_DIR = ".tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("Sample CSV Generator for ExperimentOS Demo")
print("=" * 60)

# 1. Launch Scenario
print("\n[1/4] Generating demo_launch.csv...")
df_launch = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [1000, 1200],  # 10% vs 12% (significant)
    "error_count": [10, 15]  # 0.1% vs 0.15% (OK)
})
df_launch.to_csv(f"{OUTPUT_DIR}/demo_launch.csv", index=False)
print(f"   ✅ Created: {OUTPUT_DIR}/demo_launch.csv")
print("   → Expected: Launch (Primary significant, Guardrails OK)")

# 2. Rollback Scenario
print("\n[2/4] Generating demo_rollback.csv...")
df_rollback = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [1000, 1200],  # 10% vs 12% (significant)
    "crash_count": [10, 50]  # 0.1% vs 0.5% (SEVERE: 0.4%p > 0.3%p)
})
df_rollback.to_csv(f"{OUTPUT_DIR}/demo_rollback.csv", index=False)
print(f"   ✅ Created: {OUTPUT_DIR}/demo_rollback.csv")
print("   → Expected: Rollback (Severe guardrail: crash_count Δ=0.4%p)")

# 3. Blocked Scenario
print("\n[3/4] Generating demo_blocked.csv...")
df_blocked = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [12000, 1100]  # Invalid: control conversions > users
})
df_blocked.to_csv(f"{OUTPUT_DIR}/demo_blocked.csv", index=False)
print(f"   ✅ Created: {OUTPUT_DIR}/demo_blocked.csv")
print("   → Expected: Blocked (conversions > users)")

# 4. Hold Scenario (Not Significant)
print("\n[4/4] Generating demo_hold.csv...")
df_hold = pd.DataFrame({
    "variant": ["control", "treatment"],
    "users": [10000, 10000],
    "conversions": [1000, 1050],  # 10% vs 10.5% (marginal, likely not significant)
    "error_count": [10, 12]  # OK
})
df_hold.to_csv(f"{OUTPUT_DIR}/demo_hold.csv", index=False)
print(f"   ✅ Created: {OUTPUT_DIR}/demo_hold.csv")
print("   → Expected: Hold (Primary not significant)")

# Summary
print("\n" + "=" * 60)
print("All sample CSVs generated successfully! ✅")
print("=" * 60)
print(f"\nLocation: {OUTPUT_DIR}/")
print("\nFiles:")
print("1. demo_launch.csv     → Launch scenario")
print("2. demo_rollback.csv   → Rollback scenario")
print("3. demo_blocked.csv    → Blocked scenario")
print("4. demo_hold.csv       → Hold scenario")
print("\nUsage:")
print("  streamlit run app.py")
print("  → Upload one of the above files in New Experiment page")
print("=" * 60)
