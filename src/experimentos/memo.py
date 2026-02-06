"""
Decision Memo 생성 모듈

Decision 룰 엔진 및 1pager Decision Memo 생성
"""

import logging

logger = logging.getLogger("experimentos")


def make_decision(
    health: dict,
    primary: dict,
    guardrails: list[dict] | dict,
) -> dict:
    """
    Decision Framework 룰 기반 의사결정

    Args:
        health: Health Check 결과 dict
        primary: Primary 분석 결과 dict
        guardrails: Guardrail 분석 결과 list[dict] (2-variant) 또는 dict (multi-variant)

    Returns:
        dict: {
            "decision": "Launch" | "Hold" | "Rollback",
            "reason": str,
            "details": list[str],
            "best_variant": str | None  (multi-variant only)
        }
    """
    # 룰 1: Blocked (스키마/논리 오류 또는 Severe SRM)
    if health["overall_status"] == "Blocked":
        return {
            "decision": "Hold",
            "reason": "데이터 품질 문제 (Blocked)",
            "details": health["schema"]["issues"],
        }

    # 룰 2: SRM Warning
    if health.get("srm") and health["srm"]["status"] in ["Warning", "Blocked"]:
        return {
            "decision": "Hold",
            "reason": f"SRM 탐지 (p={health['srm']['p_value']:.4f})",
            "details": [health["srm"]["message"]],
        }

    # Multi-variant dispatch
    if primary.get("is_multivariant"):
        return _make_decision_multivariant(primary, guardrails)

    # === 2-variant path (기존 로직, 변경 없음) ===
    worsened_guardrails = [g for g in guardrails if g["worsened"]]
    severe_guardrails = [g for g in guardrails if g["severe"]]

    # 룰 3: Primary 유의 + Guardrail Severe 악화 → Rollback
    if primary["is_significant"] and severe_guardrails:
        worsened_names = [g["name"] for g in severe_guardrails]
        return {
            "decision": "Rollback",
            "reason": f"심각한 Guardrail 악화: {', '.join(worsened_names)}",
            "details": [
                f"{g['name']}: {g['delta']:+.2%}p (severe threshold 초과)"
                for g in severe_guardrails
            ],
        }

    # 룰 4: Primary 유의 + Guardrail 악화 (일반) → Hold
    if primary["is_significant"] and worsened_guardrails:
        worsened_names = [g["name"] for g in worsened_guardrails]
        return {
            "decision": "Hold",
            "reason": f"Guardrail 악화: {', '.join(worsened_names)}",
            "details": [
                f"{g['name']}: {g['delta']:+.2%}p (worsened)"
                for g in worsened_guardrails
            ],
        }

    # 룰 5: Primary 유의 + Guardrail 정상 → Launch
    if primary["is_significant"]:
        return {
            "decision": "Launch",
            "reason": f"Primary 유의 (p={primary['p_value']:.4f}), Guardrail 정상",
            "details": [
                f"Absolute Lift: {primary['absolute_lift']:+.2%}p",
                f"Relative Lift: {primary['relative_lift']:+.1%}",
                f"95% CI: [{primary['ci_95'][0]:.4f}, {primary['ci_95'][1]:.4f}]",
            ],
        }

    # 룰 6: Primary 비유의 → Hold
    return {
        "decision": "Hold",
        "reason": f"Primary 비유의 (p={primary['p_value']:.4f})",
        "details": [
            "통계적으로 유의한 차이가 없습니다.",
            "추가 샘플 수집을 권장합니다.",
        ],
    }


def _make_decision_multivariant(primary: dict, guardrails: dict | list) -> dict:
    """
    Multi-variant 의사결정 룰 엔진.

    Rules:
        1. Overall chi-square 비유의 → Hold
        2. Best variant 유의(보정) + severe guardrail → Rollback
        3. Best variant 유의(보정) + worsened guardrail → Hold
        4. Best variant 유의(보정) + guardrails OK → Launch [best_variant]
        5. Overall 유의 but 개별 variant 보정 후 모두 비유의 → Hold
    """
    overall = primary.get("overall", {})
    variants = primary.get("variants", {})

    # Rule 1: Overall chi-square not significant
    if not overall.get("is_significant", False):
        return {
            "decision": "Hold",
            "reason": f"Overall 검정 비유의 (p={overall.get('p_value', 1.0):.4f})",
            "details": ["전체 variant 간 유의한 차이가 없습니다.", "추가 샘플 수집을 권장합니다."],
            "best_variant": None,
        }

    # Find best variant (highest corrected-significant lift)
    best_variant = _find_best_variant(variants)

    if best_variant is None:
        # Rule 5: Overall significant but no individual variant significant after correction
        return {
            "decision": "Hold",
            "reason": "개별 variant 보정 후 모두 비유의",
            "details": [
                "Overall 검정은 유의하나, 다중 비교 보정 후 개별 variant가 유의하지 않습니다.",
                "추가 샘플 수집 또는 variant 수 조정을 권장합니다.",
            ],
            "best_variant": None,
        }

    best_data = variants[best_variant]

    # Collect guardrail info for the best variant
    severe_list, worsened_list = _collect_guardrail_flags(guardrails, best_variant)

    # Rule 2: Best variant significant + severe guardrail → Rollback
    if severe_list:
        return {
            "decision": "Rollback",
            "reason": f"심각한 Guardrail 악화 ({best_variant}): {', '.join(g['name'] for g in severe_list)}",
            "details": [
                f"{g['name']}: {g['delta']:+.2%}p (severe threshold 초과)"
                for g in severe_list
            ],
            "best_variant": best_variant,
        }

    # Rule 3: Best variant significant + worsened guardrail → Hold
    if worsened_list:
        return {
            "decision": "Hold",
            "reason": f"Guardrail 악화 ({best_variant}): {', '.join(g['name'] for g in worsened_list)}",
            "details": [
                f"{g['name']}: {g['delta']:+.2%}p (worsened)"
                for g in worsened_list
            ],
            "best_variant": best_variant,
        }

    # Rule 4: Best variant significant + guardrails OK → Launch
    return {
        "decision": "Launch",
        "reason": (
            f"{best_variant} 유의 "
            f"(p_corrected={best_data.get('p_value_corrected', best_data['p_value']):.4f}), "
            f"Guardrail 정상"
        ),
        "details": [
            f"Best Variant: {best_variant}",
            f"Absolute Lift: {best_data['absolute_lift']:+.2%}p",
            f"Relative Lift: {best_data['relative_lift']:+.1%}" if best_data.get("relative_lift") is not None else "Relative Lift: N/A",
            f"95% CI: [{best_data['ci_95'][0]:.4f}, {best_data['ci_95'][1]:.4f}]",
        ],
        "best_variant": best_variant,
    }


def _find_best_variant(variants: dict) -> str | None:
    """Find the best significant (corrected) variant by highest absolute lift."""
    best_name = None
    best_lift = -float("inf")
    for name, data in variants.items():
        if data.get("is_significant_corrected", False) and data["absolute_lift"] > best_lift:
            best_lift = data["absolute_lift"]
            best_name = name
    return best_name


def _collect_guardrail_flags(
    guardrails: dict | list,
    variant_name: str,
) -> tuple[list[dict], list[dict]]:
    """
    Extract severe and worsened guardrail lists for a specific variant.

    Supports both multi-variant format (dict with by_variant) and legacy list format.
    """
    severe: list[dict] = []
    worsened: list[dict] = []

    if isinstance(guardrails, dict) and "by_variant" in guardrails:
        variant_guardrails = guardrails.get("by_variant", {}).get(variant_name, [])
        for g in variant_guardrails:
            if g.get("severe"):
                severe.append(g)
            elif g.get("worsened"):
                worsened.append(g)
    elif isinstance(guardrails, list):
        for g in guardrails:
            if g.get("severe"):
                severe.append(g)
            elif g.get("worsened"):
                worsened.append(g)

    return severe, worsened


def generate_memo(
    experiment_name: str,
    decision: dict,
    health: dict,
    primary: dict,
    guardrails: list[dict] | dict,
    bayesian_insights: dict | None = None,
    charter: dict | None = None,
) -> str:
    """
    Decision Memo (1pager) Markdown 생성
    
    Args:
        experiment_name: 실험명
        decision: make_decision() 결과
        health: Health Check 결과
        primary: Primary 분석 결과
        guardrails: Guardrail 분석 결과
        bayesian_insights: Optional Bayesian 분석 결과
        charter: Optional experiment charter with hypothesis, primary_metric, target_sample_size
    
    Returns:
        str: Markdown 형식 1pager
    """
    from datetime import datetime
    
    # 현재 날짜
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Decision 배지
    decision_text = decision["decision"]
    if decision_text == "Launch":
        decision_badge = "🚀 **Launch**"
    elif decision_text == "Rollback":
        decision_badge = "🔙 **Rollback**"
    else:
        decision_badge = "⏸️ **Hold**"
    
    # 1. Summary
    # Charter Section (PR2)
    if charter is None:
        charter = {}
    charter_md = ""
    if charter.get("hypothesis") or charter.get("target_sample_size"):
        charter_md = f"""
## 📜 Experiment Charter
- **Hypothesis**: {charter.get('hypothesis', '(Not specificed)')}
- **Primary Metric**: {charter.get('primary_metric', '(Not specified)')}
- **Target Sample Size**: {f"{charter['target_sample_size']:,} per variation" if charter.get('target_sample_size') else "N/A"}

---
"""

    md_content = f"""
# 📝 Decision Memo: {experiment_name}
**Export Date**: {today}

## 📊 Executive Summary
{charter_md}
## 🚦 Final Decision
- **Decision**: **{decision["decision"]}**
- **Reason**: {decision["reason"]}
"""
    
    # 2. Primary Result
    is_multi = primary.get("is_multivariant", False)

    if is_multi:
        primary_section = _generate_primary_section_multivariant(primary, decision)
    else:
        primary_section = f"""
---

## 📊 Primary Result (Conversion Rate)

- **Control**: {primary['control']['rate']:.2%} ({primary['control']['conversions']:,} / {primary['control']['users']:,})
- **Treatment**: {primary['treatment']['rate']:.2%} ({primary['treatment']['conversions']:,} / {primary['treatment']['users']:,})
- **Absolute Lift**: {primary['absolute_lift']:+.2%}p
- **Relative Lift**: {primary['relative_lift']:+.1%}
- **95% CI**: [{primary['ci_95'][0]:.4f}, {primary['ci_95'][1]:.4f}]
- **P-value**: {primary['p_value']:.6f}
- **Statistical Significance**: {'✅ Yes' if primary['is_significant'] else '❌ No'}
"""

    # 3. Guardrails
    guardrail_section = "\n---\n\n## 🛡️ Guardrails\n\n"

    if is_multi and isinstance(guardrails, dict):
        guardrail_section += _generate_guardrail_section_multivariant(guardrails)
    elif isinstance(guardrails, list) and guardrails:
        guardrail_table = "| Metric | Control | Treatment | Δ | Status |\n|--------|---------|-----------|---|--------|\n"
        for g in guardrails:
            status = "🚫 Severe" if g["severe"] else ("⚠️ Worsened" if g["worsened"] else "✅ OK")
            guardrail_table += f"| {g['name']} | {g['control_rate']:.2%} | {g['treatment_rate']:.2%} | {g['delta']:+.2%}p | {status} |\n"
        guardrail_section += guardrail_table
    else:
        guardrail_section += "No guardrails specified.\n"
    
    # 4. Health Check
    health_section = f"""
---

## 🩺 Health Check

- **Overall Status**: {health['overall_status']}
"""
    
    if health.get("srm"):
        srm = health["srm"]
        health_section += f"- **SRM Status**: {srm['status']} (p={srm['p_value']:.4f})\n"
    
    # 5. Decision Details
    decision_details_section = "\n---\n\n## 🎯 Decision Details\n\n"
    for detail in decision["details"]:
        decision_details_section += f"- {detail}\n"
    
    # 6. Next Actions
    next_actions = """
---

## 🚀 Next Actions

"""
    
    if decision_text == "Launch":
        next_actions += """- Proceed with full rollout
- Monitor key metrics post-launch
- Document learnings
"""
    elif decision_text == "Rollback":
        next_actions += """- Halt experiment immediately
- Investigate root cause of guardrail degradation
- Revisit experiment design
"""
    else:  # Hold
        next_actions += """- Do not launch at this time
- Review data quality or wait for more data
- Re-evaluate when conditions improve
"""
    
    # 7. Additional Evidence (Informational Only) - Bayesian
    evidence_section = ""
    if bayesian_insights and bayesian_insights.get("conversion"):
        evidence_section = "\n---\n\n## ℹ️ Additional Evidence (Bayesian)\n\n> Note: This section is informational and did not influence the decision.\n\n"
        
        # Primary Conversion
        b_conv = bayesian_insights["conversion"]
        prob = b_conv["prob_treatment_beats_control"]
        loss = b_conv["expected_loss"]
        evidence_section += f"- **Primary Metric**: P(Treatment > Control) = {prob:.1%}, Expected Loss = {loss:.6f}\n"
        
        # Continuous
        if bayesian_insights.get("continuous"):
            for metric, res in bayesian_insights["continuous"].items():
                p = res["prob_treatment_beats_control"]
                evidence_section += f"- **{metric}**: P(Treatment > Control) = {p:.1%}\n"


    
    # 7. Assumptions & Thresholds (새로 추가)
    from .config import config
    assumptions = config.get_assumptions_text()
    
    # 조합
    memo = (md_content + primary_section + guardrail_section + 
            health_section + decision_details_section + 
            next_actions + evidence_section + assumptions)
    
    return memo


def _generate_primary_section_multivariant(primary: dict, decision: dict) -> str:
    """Generate multi-variant primary result section for memo."""
    overall = primary.get("overall", {})
    control = primary.get("control_stats", {})
    variants = primary.get("variants", {})
    best = decision.get("best_variant")

    section = f"""
---

## 📊 Primary Result (Multi-Variant Conversion Rate)

### Overall Test
- **Chi-square Statistic**: {overall.get('chi2_stat', 0):.4f}
- **P-value**: {overall.get('p_value', 1.0):.6f}
- **Degrees of Freedom**: {overall.get('dof', 0)}
- **Significant**: {'✅ Yes' if overall.get('is_significant') else '❌ No'}

### Control
- **Rate**: {control.get('rate', 0):.2%} ({control.get('conversions', 0):,} / {control.get('users', 0):,})

### Per-Variant Comparisons vs Control

| Variant | Rate | Absolute Lift | Relative Lift | P-value | P (corrected) | Significant |
|---------|------|--------------|--------------|---------|---------------|-------------|
"""
    for v_name, v_data in variants.items():
        is_best = " ⭐" if v_name == best else ""
        rel = f"{v_data['relative_lift']:+.1%}" if v_data.get("relative_lift") is not None else "N/A"
        p_corr = v_data.get("p_value_corrected", v_data["p_value"])
        sig = "✅" if v_data.get("is_significant_corrected", False) else "❌"
        section += (
            f"| {v_name}{is_best} | {v_data['rate']:.2%} | {v_data['absolute_lift']:+.2%}p "
            f"| {rel} | {v_data['p_value']:.4f} | {p_corr:.4f} | {sig} |\n"
        )

    if best:
        section += f"\n**Best Variant**: {best}\n"

    return section


def _generate_guardrail_section_multivariant(guardrails: dict) -> str:
    """Generate multi-variant guardrail section for memo."""
    by_variant = guardrails.get("by_variant", {})
    summary = guardrails.get("summary", [])

    if not by_variant:
        return "No guardrails specified.\n"

    section = "### Summary\n\n"
    if guardrails.get("any_severe"):
        section += "⚠️ **Severe guardrail degradation detected.**\n\n"
    elif guardrails.get("any_worsened"):
        section += "⚠️ **Guardrail worsening detected.**\n\n"
    else:
        section += "✅ All guardrails healthy across all variants.\n\n"

    if summary:
        section += "| Metric | Worst Variant | Worst Δ | Status |\n|--------|--------------|---------|--------|\n"
        for s in summary:
            status = "🚫 Severe" if s["severe"] else ("⚠️ Worsened" if s["worsened"] else "✅ OK")
            section += f"| {s['name']} | {s['worst_variant']} | {s['worst_delta']:+.2%}p | {status} |\n"
        section += "\n"

    # Detailed per-variant tables
    for v_name, v_guardrails in by_variant.items():
        section += f"### {v_name}\n\n"
        section += "| Metric | Control | Treatment | Δ | Status |\n|--------|---------|-----------|---|--------|\n"
        for g in v_guardrails:
            status = "🚫 Severe" if g["severe"] else ("⚠️ Worsened" if g["worsened"] else "✅ OK")
            section += f"| {g['name']} | {g['control_rate']:.2%} | {g['treatment_rate']:.2%} | {g['delta']:+.2%}p | {status} |\n"
        section += "\n"

    return section


def export_html(markdown_content: str) -> str:
    """
    Markdown을 HTML로 변환
    
    Args:
        markdown_content: Markdown 문자열
    
    Returns:
        str: HTML 문자열
    """
    import markdown
    
    html_body = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code']
    )
    
    # HTML 템플릿
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decision Memo</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        h2 {{
            margin-top: 30px;
            color: #555;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 30px 0;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    return html
