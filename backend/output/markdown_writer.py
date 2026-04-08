"""
KairosAI — Markdown Writer
----------------------------
Converts the final decision dict into a clean, readable Markdown report.
"""

from datetime import datetime
from pathlib import Path


VERDICT_EMOJI = {
    "PROCEED":   "✅",
    "PAUSE":     "⏸️",
    "ROLL_BACK": "🔴",
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
}

PRIORITY_EMOJI = {
    "P0": "🚨",
    "P1": "⚡",
    "P2": "📋",
}


def write_markdown_report(decision: dict, reports_dir: str = "reports") -> str:
    """
    Generate a Markdown report from the final decision dict.

    Returns:
        Path to the written .md file.
    """
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session_id = decision.get("meta", {}).get("session_id", "unknown")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"warroom_{session_id}_{ts}.md"
    filepath = out_dir / filename

    md = _build_markdown(decision)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    return str(filepath)


def _build_markdown(d: dict) -> str:
    meta      = d.get("meta", {})
    verdict   = d.get("decision", "UNKNOWN")
    conf      = d.get("confidence", {})
    rationale = d.get("rationale", {})
    risks     = d.get("risk_register", [])
    actions   = d.get("action_plan", {})
    comms     = d.get("communication_plan", {})
    debate    = d.get("debate_summary", {})
    verdicts  = d.get("agent_verdicts", [])
    stats     = d.get("session_stats", {})

    emoji  = VERDICT_EMOJI.get(verdict, "❓")
    label  = {"PROCEED": "PROCEED", "PAUSE": "PAUSE", "ROLL_BACK": "ROLL BACK"}.get(verdict, verdict)
    now    = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = []

    # ── Header ────────────────────────────────────────────────────────
    lines += [
        f"# {emoji} KairosAI War Room — {label}",
        "",
        f"**Product:** {meta.get('product', 'PurpleMerit — SmartDash 2.0')}  ",
        f"**Session:** `{meta.get('session_id', '—')}`  ",
        f"**Generated:** {now}  ",
        f"**Agents run:** {', '.join(meta.get('agents_run', []))}",
        "",
        "---",
        "",
    ]

    # ── Decision block ─────────────────────────────────────────────────
    lines += [
        "## Decision",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| **Verdict** | {emoji} **{label}** |",
        f"| **Confidence score** | {conf.get('weighted_score', '—')}/100 |",
        f"| **Interpretation** | {conf.get('interpretation', '—')} |",
        f"| **Agent agreement** | {int(conf.get('agreement_ratio', 0) * 100)}% |",
        f"| **Verdict tally** | {_format_tally(conf.get('verdict_distribution', {}))} |",
        "",
        "---",
        "",
    ]

    # ── Rationale ──────────────────────────────────────────────────────
    lines += [
        "## Rationale",
        "",
        "### Primary drivers",
        "",
    ]
    for driver in rationale.get("primary_drivers", []):
        lines.append(f"- {driver}")

    lines += ["", "### Metric references", ""]
    for ref in rationale.get("metric_references", []):
        lines.append(f"- {ref}")

    if rationale.get("feedback_summary"):
        lines += ["", "### User feedback summary", "", rationale["feedback_summary"]]

    if rationale.get("debate_resolution"):
        lines += ["", "### Debate resolution", "", f"> {rationale['debate_resolution']}"]

    lines += ["", "---", ""]

    # ── Risk Register ──────────────────────────────────────────────────
    lines += [
        "## Risk Register",
        "",
        "| Severity | Risk | Mitigation | Owner |",
        "|---|---|---|---|",
    ]
    for risk in risks:
        sev   = risk.get("severity", "low")
        emoji_s = SEVERITY_EMOJI.get(sev, "")
        r_text  = risk.get("risk", "")[:70]
        mit     = risk.get("mitigation", "—")[:60]
        owner   = risk.get("owner", risk.get("source_agent", "—"))
        lines.append(f"| {emoji_s} {sev.capitalize()} | {r_text} | {mit} | {owner} |")

    lines += ["", "---", ""]

    # ── Action Plan ────────────────────────────────────────────────────
    lines += ["## Action Plan", ""]

    for window, window_label in [
        ("immediate",  "🚨 Immediate (now)"),
        ("within_24h", "⚡ Within 24 hours"),
        ("within_48h", "📋 Within 48 hours"),
    ]:
        window_actions = actions.get(window, [])
        if not window_actions:
            continue
        lines += [f"### {window_label}", ""]
        for a in window_actions:
            pri   = PRIORITY_EMOJI.get(a.get("priority", "P2"), "")
            act   = a.get("action", "")
            owner = a.get("owner", "?")
            lines.append(f"- {pri} **[{owner}]** {act}")
        lines.append("")

    lines += ["---", ""]

    # ── Communication Plan ─────────────────────────────────────────────
    lines += [
        "## Communication Plan",
        "",
        f"**Internal:** {comms.get('internal_message', '—')}",
        "",
        f"**User-facing:** {comms.get('user_message', '—')}",
        "",
        f"**Enterprise accounts:** {comms.get('enterprise_message', '—')}",
        "",
        "---",
        "",
    ]

    # ── Agent Verdicts ─────────────────────────────────────────────────
    lines += [
        "## Agent Verdicts",
        "",
        "| Agent | Verdict | Confidence | Summary |",
        "|---|---|---|---|",
    ]
    for av in verdicts:
        v_emoji = VERDICT_EMOJI.get(av.get("verdict", ""), "")
        summary = av.get("summary", "")[:80]
        lines.append(
            f"| {av.get('agent_name', av.get('agent',''))} "
            f"| {v_emoji} {av.get('verdict','')} "
            f"| {av.get('confidence','')} "
            f"| {summary} |"
        )

    lines += ["", "---", ""]

    # ── Debate Summary ─────────────────────────────────────────────────
    if debate:
        lines += [
            "## Debate Summary",
            "",
            f"**Consensus:** {'Yes' if debate.get('consensus_exists') else 'No — agents were split'}  ",
            f"**Core tension:** {debate.get('tension', '—')}  ",
            f"**Resolved verdict:** {VERDICT_EMOJI.get(debate.get('resolved_verdict',''), '')} {debate.get('resolved_verdict', '—')} (confidence: {debate.get('resolved_confidence', '—')})  ",
            f"**Key unresolved question:** {debate.get('key_unresolved', '—')}",
            "",
            "---",
            "",
        ]

    # ── Confidence Boosters ────────────────────────────────────────────
    boosters = conf.get("boosters", [])
    if boosters:
        lines += [
            "## What Would Increase Confidence",
            "",
        ]
        for b in boosters:
            lines.append(f"- {b}")
        lines.append("")

    # ── Session Stats ──────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## Session Statistics",
        "",
        f"- Total agents: {stats.get('total_agents', '—')}",
        f"- Verdict tally: {_format_tally(stats.get('verdict_tally', {}))}",
        f"- Average agent confidence: {stats.get('avg_confidence', '—')}",
        f"- Total events logged: {stats.get('total_events', '—')}",
        "",
        "*Generated by KairosAI — multi-agent launch intelligence platform*",
    ]

    return "\n".join(lines)


def _format_tally(tally: dict) -> str:
    if not tally:
        return "—"
    parts = []
    for verdict, count in tally.items():
        emoji = VERDICT_EMOJI.get(verdict, "")
        parts.append(f"{emoji} {verdict}: {count}")
    return " | ".join(parts)