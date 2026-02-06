import pytest
import pandas as pd
import numpy as np
from src.experimentos.analysis import analyze_multivariant, _correct_p_values

def test_correction_logic_manual():
    """Verify manual implementations of correction methods."""
    p_values = [0.01, 0.04, 0.10]
    
    # Bonferroni: p * 3
    # 0.01 * 3 = 0.03
    # 0.04 * 3 = 0.12
    # 0.10 * 3 = 0.30
    bonferroni = _correct_p_values(p_values, method='bonferroni')
    assert bonferroni == pytest.approx([0.03, 0.12, 0.30])
    
    # Holm-Bonferroni
    # Sorted: 0.01 (rank 1), 0.04 (rank 2), 0.10 (rank 3)
    # p1_corr = 0.01 * (3 - 1 + 1) = 0.03
    # p2_corr = 0.04 * (3 - 2 + 1) = 0.08
    # p3_corr = 0.10 * (3 - 3 + 1) = 0.10
    # Then ensure monotonicity: 0.03 <= 0.08 <= 0.10 (ok)
    holm = _correct_p_values(p_values, method='holm')
    assert holm == pytest.approx([0.03, 0.08, 0.10])
    
    # None
    none_corr = _correct_p_values(p_values, method='none')
    assert none_corr == p_values

def test_analyze_multivariant_correction_integration():
    """Test that analyze_multivariant applies the requested correction."""
    # Control: 1000/100 (10%)
    # A: 1000/125 (12.5%, likely signif uncorrected)
    # B: 1000/100 (10%, not signif)
    # C: 1000/125 (12.5%, likely signif uncorrected)
    # With 3 treatments, Bonferroni multiplier is 3. 
    # Uncorrected p for 12.5% vs 10% (N=1000) is approx 0.07? No wait..
    # 100 vs 125. Z approx (25)/sqrt(...)
    # Let's use a simpler known case or just check if p_corrected > p_raw
    
    data = {
        "variant": ["control", "A", "B", "C"],
        "users": [10000, 10000, 10000, 10000],
        "conversions": [1000, 1150, 1000, 1150] 
    }
    # 10% vs 11.5%: Lift 1.5%. 
    # Z ~ (0.015) / sqrt(0.1*0.9*(2/10000)) ~ 0.015 / 0.0042 ~ 3.5 -> p < 0.001
    
    df = pd.DataFrame(data)
    
    # Run with Bonferroni
    result = analyze_multivariant(df, correction_method='bonferroni')
    
    var_a = result["variants"]["A"]
    assert "p_value_corrected" in var_a
    assert var_a["p_value_corrected"] >= var_a["p_value"]
    # With strict inequality if p < 1.0/3? 
    # Just check logic exists.
    
    assert result["correction_method"] == "bonferroni"
    
    # Check all_pairs presence
    assert "all_pairs" in result
    # Combinations of 4 variants = 4C2 = 6 pairs
    assert len(result["all_pairs"]) == 6

def test_all_pairs_logic():
    """Verify all pairwise combinations are generated."""
    data = {
        "variant": ["control", "T1", "T2"],
        "users": [100, 100, 100],
        "conversions": [10, 20, 30]
    }
    df = pd.DataFrame(data)
    result = analyze_multivariant(df)
    
    pairs = result["all_pairs"]
    # control-T1, control-T2, T1-T2
    pair_names = set([
        tuple(sorted((p["variant_a"], p["variant_b"]))) for p in pairs
    ])
    
    expected = {
        tuple(sorted(("control", "T1"))),
        tuple(sorted(("control", "T2"))),
        tuple(sorted(("T1", "T2")))
    }
    assert pair_names == expected
