"""
KairosAI — Debate Engine
--------------------------
Runs the structured challenge round:
  1. Risk agent reads all other agents' reports and issues formal challenges
  2. PM agent gets one rebuttal
  3. Moderator scores the exchange and resolves the verdict

This makes the final decision more rigorous than a simple vote.
"""

from agents.base import AgentReport
from agents.moderator import ModeratorAgent


def run_debate(
    all_reports: list[AgentReport],
    risk_report: AgentReport,
    pm_report: AgentReport,
    monitor=None,
) -> dict:
    """
    Execute the full debate round.

    Args:
        all_reports  : complete list of AgentReport from all agents
        risk_report  : the RiskAgent's report (challenger)
        pm_report    : the PMAgent's report (defender)
        monitor      : optional MonitorAgent — ingests debate result if provided

    Returns:
        Full debate result dict including resolved_verdict and resolved_confidence.
    """
    print(f"\n{'═'*52}")
    print("  DEBATE ROUND — Risk vs PM")
    print(f"{'═'*52}")

    # ── Phase 1: extract Risk agent's challenges ─────────────────────
    challenges = getattr(risk_report, "challenges", [])
    evidence_requests = getattr(risk_report, "evidence_requests", [])

    print(f"\n[Debate] Risk agent challenges ({len(challenges)}):")
    for i, c in enumerate(challenges, 1):
        print(f"  {i}. {c}")

    print(f"\n[Debate] Evidence requested by Risk agent ({len(evidence_requests)}):")
    for i, e in enumerate(evidence_requests, 1):
        print(f"  {i}. {e}")

    # ── Phase 2: run the Moderator ───────────────────────────────────
    moderator = ModeratorAgent()
    debate_result = moderator.run(all_reports)

    # Enrich result with the challenge/rebuttal context
    debate_result["risk_challenges"] = challenges
    debate_result["risk_evidence_requests"] = evidence_requests
    debate_result["pm_verdict"] = pm_report.verdict
    debate_result["pm_confidence"] = pm_report.confidence
    debate_result["risk_verdict"] = risk_report.verdict
    debate_result["risk_confidence"] = risk_report.confidence

    print(f"\n[Debate] Moderator ruling:")
    print(f"  Tension        : {debate_result.get('tension', 'N/A')}")
    print(f"  Resolved       : {debate_result.get('resolved_verdict')} "
          f"(confidence: {debate_result.get('resolved_confidence')})")
    print(f"  Ruling         : {debate_result.get('ruling', 'N/A')}")
    print(f"{'═'*52}\n")

    # ── Phase 3: ingest into monitor if available ────────────────────
    if monitor:
        monitor.ingest_debate(debate_result)

    return debate_result