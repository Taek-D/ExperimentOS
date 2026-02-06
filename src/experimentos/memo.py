"""
Decision Memo 생성 모듈

Decision 룰 엔진 및 1pager Decision Memo 생성
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger("experimentos")


def make_decision(
    health: Dict,
    primary: Dict,
    guardrails: List[Dict]
) -> Dict:
    """
    Decision Framework 룰 기반 의사결정
    
    Args:
        health: Health Check 결과 dict
        primary: Primary 분석 결과 dict
        guardrails: Guardrail 분석 결과 list of dict
    
    Returns:
        dict: {
            "decision": "Launch" | "Hold" | "Rollback",
            "reason": str,  # 결론 근거 (한 줄)
            "details": List[str]  # 상세 근거
        }
    """
    details: list[str] = []
    
    # 룰 1: Blocked (스키마/논리 오류 또는 Severe SRM)
    if health["overall_status"] == "Blocked":
        return {
            "decision": "Hold",
            "reason": "데이터 품질 문제 (Blocked)",
            "details": health["schema"]["issues"]
        }
    
    # 룰 2: SRM Warning
    if health.get("srm") and health["srm"]["status"] in ["Warning", "Blocked"]:
        return {
            "decision": "Hold",
            "reason": f"SRM 탐지 (p={health['srm']['p_value']:.4f})",
            "details": [health["srm"]["message"]]
        }
    
    # Guardrail 악화 여부 확인
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
            ]
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
            ]
        }
    
    # 룰 5: Primary 유의 + Guardrail 정상 → Launch
    if primary["is_significant"]:
        return {
            "decision": "Launch",
            "reason": f"Primary 유의 (p={primary['p_value']:.4f}), Guardrail 정상",
            "details": [
                f"Absolute Lift: {primary['absolute_lift']:+.2%}p",
                f"Relative Lift: {primary['relative_lift']:+.1%}",
                f"95% CI: [{primary['ci_95'][0]:.4f}, {primary['ci_95'][1]:.4f}]"
            ]
        }
    
    # 룰 6: Primary 비유의 → Hold
    return {
        "decision": "Hold",
        "reason": f"Primary 비유의 (p={primary['p_value']:.4f})",
        "details": [
            "통계적으로 유의한 차이가 없습니다.",
            "추가 샘플 수집을 권장합니다."
        ]
    }


def generate_memo(
    experiment_name: str,
    decision: Dict,
    health: Dict,
    primary: Dict,
    guardrails: List[Dict],
    bayesian_insights: Optional[Dict] = None,
    charter: Optional[Dict] = None
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
    
    if guardrails:
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
