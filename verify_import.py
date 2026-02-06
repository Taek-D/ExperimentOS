import sys
sys.path.append(".")
try:
    from src.experimentos.integrations.statsig import StatsigProvider
    print("StatsigProvider imported successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
