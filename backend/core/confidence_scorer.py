"""
KairosAI — Confidence Scorer
------------------------------
Computes a single weighted confidence score from all agent reports.

Each agent role has a different weight based on its relevance to
a launch decision. The final score reflects both how confident agents
are AND whether they agree with each other.
"""

from agents.base import AgentReport


# How much each agent's confidence vote counts toward the final score.
# Weights sum to 1.0.
AGENT_WEIGHTS: dict[str, float] = {
    "Data Analyst":      0.25,   # highest — objective numbers
    "SRE / Engineering": 0.22,   # infra truth — crashes are hard facts
    "Risk / Critic":     0.20,   # devil's advocate — penalises overconfidence
    "Product Manager":   0.18,   # success criteria owner
    "Marketing / Comms": 0.10,   # perception matters but softer signal
    "Debate Moderator":  0.05,   # tie-breaker weight
}

DEFAULT_WEIGHT = 0.10  # for any agent not in the table


def compute_confidence(
    agent_reports: list[AgentReport],
    debate_result: dict | None = None,
) -> dict:
    """
    Compute the final weighted confidence score.

    Args:
        agent_reports : list of AgentReport from all agents
        debate_result : optional moderated result from ModeratorAgent

    Returns:
        dict with:
            weighted_score      : int 0-100
            raw_avg             : float
            agreement_bonus     : int  (added when agents agree)
            agreement_penalty   : int  (subtracted when agents disagree sharply)
            verdict_distribution: dict
            per_agent           : list of per-agent breakdowns
            interpretation      : str
            confidence_boosters : list[str]  — what would raise confidence
    """

    if not agent_reports:
        return {"weighted_score": 0, "error": "No agent reports provided."}

    # ── Step 1: weighted average confidence ───────────────────────────
    total_weight = 0.0
    weighted_sum = 0.0
    per_agent = []

    for report in agent_reports:
        weight = AGENT_WEIGHTS.get(report.agent_name, DEFAULT_WEIGHT)
        weighted_sum += report.confidence * weight
        total_weight += weight
        per_agent.append({
            "agent":      report.agent_name,
            "verdict":    report.verdict,
            "confidence": report.confidence,
            "weight":     weight,
            "contribution": round(report.confidence * weight, 1),
        })

    # Include debate moderator if available
    if debate_result and "resolved_confidence" in debate_result:
        mod_weight = AGENT_WEIGHTS.get("Debate Moderator", DEFAULT_WEIGHT)
        mod_conf = debate_result["resolved_confidence"]
        weighted_sum += mod_conf * mod_weight
        total_weight += mod_weight
        per_agent.append({
            "agent":      "Debate Moderator",
            "verdict":    debate_result.get("resolved_verdict", "PAUSE"),
            "confidence": mod_conf,
            "weight":     mod_weight,
            "contribution": round(mod_conf * mod_weight, 1),
        })

    raw_weighted = weighted_sum / total_weight if total_weight > 0 else 50.0
    raw_avg = sum(r.confidence for r in agent_reports) / len(agent_reports)

    # ── Step 2: agreement adjustment ──────────────────────────────────
    verdicts = [r.verdict for r in agent_reports]
    verdict_counts = {v: verdicts.count(v) for v in set(verdicts)}
    majority_count = max(verdict_counts.values())
    total_agents = len(verdicts)

    agreement_ratio = majority_count / total_agents

    if agreement_ratio == 1.0:
        # Perfect consensus
        agreement_bonus = 8
        agreement_penalty = 0
    elif agreement_ratio >= 0.75:
        # Strong majority
        agreement_bonus = 4
        agreement_penalty = 0
    elif agreement_ratio >= 0.5:
        # Simple majority
        agreement_bonus = 0
        agreement_penalty = 0
    else:
        # No majority — agents are split
        agreement_bonus = 0
        agreement_penalty = 10

    # ── Step 3: final score ───────────────────────────────────────────
    final_score = int(raw_weighted + agreement_bonus - agreement_penalty)
    final_score = max(0, min(100, final_score))

    # ── Step 4: interpretation ────────────────────────────────────────
    if final_score >= 80:
        interpretation = "High confidence — strong evidence supports the verdict."
    elif final_score >= 65:
        interpretation = "Moderate confidence — verdict is supported but some uncertainty remains."
    elif final_score >= 50:
        interpretation = "Low confidence — agents are split or data is insufficient."
    else:
        interpretation = "Very low confidence — major disagreement or missing evidence."

    # ── Step 5: what would boost confidence ───────────────────────────
    boosters = _identify_boosters(agent_reports, agreement_ratio, debate_result)

    return {
        "weighted_score":       final_score,
        "raw_avg":              round(raw_avg, 1),
        "raw_weighted":         round(raw_weighted, 1),
        "agreement_bonus":      agreement_bonus,
        "agreement_penalty":    agreement_penalty,
        "agreement_ratio":      round(agreement_ratio, 2),
        "verdict_distribution": verdict_counts,
        "per_agent":            per_agent,
        "interpretation":       interpretation,
        "confidence_boosters":  boosters,
    }


def _identify_boosters(
    reports: list[AgentReport],
    agreement_ratio: float,
    debate_result: dict | None,
) -> list[str]:
    """Identify what additional evidence would raise confidence."""
    boosters = []

    if agreement_ratio < 0.75:
        boosters.append(
            "Agent consensus — currently split verdicts reduce confidence. "
            "Aligning Risk and PM agents would add +10 points."
        )

    # Check if any agent has low raw confidence
    low_conf = [r for r in reports if r.confidence < 60]
    if low_conf:
        names = [r.agent_name for r in low_conf]
        boosters.append(
            f"{', '.join(names)} expressed low confidence (<60). "
            "Providing more granular data (hourly metrics, user cohort breakdown) would help."
        )

    boosters.append(
        "3+ consecutive days of improving metrics (currently only 2 recovery days) "
        "would confirm the hot-patch is working."
    )
    boosters.append(
        "Root cause confirmation from engineering (fix deployed + verified) "
        "would raise SRE and Risk agent confidence significantly."
    )
    boosters.append(
        "Payment integrity audit completion — confirming no remaining duplicate "
        "charge risk would remove the highest-severity open risk."
    )

    return boosters[:4]  # top 4 boosters