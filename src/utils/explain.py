def format_issue(issue):
    entities = issue.get("matched_entities", {})
    evidence = issue.get("evidence", {})
    sources = evidence.get("sources", [])

    drug = entities.get("drug", "UNKNOWN")
    condition = entities.get("condition", "UNKNOWN")

    lines = []

    # -------------------------
    # HEADER
    # -------------------------
    lines.append(f"Rule: {issue.get('rule_id', 'N/A')}")
    lines.append(f"Drug: {drug}")
    lines.append(f"Condition: {condition}")
    lines.append("")

    # -------------------------
    # RISK
    # -------------------------
    risk = issue.get("risk")
    if risk:
        lines.append("Risk:")
        lines.append(f"{risk}")
        lines.append("")

    # -------------------------
    # EXPLANATION
    # -------------------------
    msg = issue.get("message")
    if msg:
        lines.append("Explanation:")
        lines.append(f"{msg}")
        lines.append("")

    # -------------------------
    # EVIDENCE (MULTIPLE SOURCES)
    # -------------------------
    if sources:
        lines.append("Evidence:")
        for s in sources:
            title = s.get("title", "")
            year = s.get("year", "")
            lines.append(f"- {title} ({year})")

    return "\n".join(lines)