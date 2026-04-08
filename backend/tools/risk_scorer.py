"""
KairosAI — Tool: risk_scorer
------------------------------
Generates a scored risk register by combining:
  - Metric signals (from aggregate/anomaly tools)
  - Feedback signals (from sentiment tool)
  - Known issues (from release_notes)
  - Pre-defined risk catalogue for this type of launch

Each risk gets a Likelihood (1-5) × Impact (1-5) = Risk Score (1-25).
Risks are ranked and assigned a response category.

Called by: Risk/Critic Agent, Orchestrator
"""

from typing import TypedDict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.metrics import get_latest, KPI_THRESHOLDS
from data.release_notes import get_known_issues, get_rollback_info


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class Risk(TypedDict):
    id: str
    category: str           # "technical" | "business" | "reputational" | "operational"
    title: str
    description: str
    likelihood: int         # 1-5
    impact: int             # 1-5
    score: int              # likelihood × impact (1-25)
    rating: str             # "critical" (20-25) | "high" (12-19) | "medium" (6-11) | "low" (1-5)
    evidence: list[str]     # metric/feedback signals driving this assessment
    mitigation: str
    owner: str
    response: str           # "immediate" | "24h" | "48h" | "monitor"


class RiskRegister(TypedDict):
    total_risks: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    top_risks: list[Risk]       # top 5 by score
    risk_by_category: dict[str, int]
    recommended_posture: str    # "proceed" | "pause" | "rollback"
    posture_rationale: str
    risks: list[Risk]


# ---------------------------------------------------------------------------
# Risk catalogue — pre-defined risks that get dynamically scored
# ---------------------------------------------------------------------------

def _build_risk_catalogue(latest_metrics: dict, known_issues: list[dict]) -> list[dict]:
    """
    Build the risk catalogue with dynamic scoring based on live signals.
    Each risk has base likelihood/impact, adjusted by observed data.
    """
    crash_rate = latest_metrics.get("crash_rate", 0)
    payment_success = latest_metrics.get("payment_success_rate", 100)
    p95 = latest_metrics.get("p95_latency_ms", 0)
    support_tickets = latest_metrics.get("support_tickets", 0)
    daily_churn = latest_metrics.get("daily_churn", 0)
    retention_d1 = latest_metrics.get("retention_d1", 100)

    critical_issues = [i for i in known_issues if i["severity"] == "critical"]
    high_issues = [i for i in known_issues if i["severity"] == "high"]

    return [
        # ------------------------------------------------------------------
        # TECHNICAL RISKS
        # ------------------------------------------------------------------
        {
            "id": "R-001",
            "category": "technical",
            "title": "iOS app crash causing user data loss",
            "description": (
                "iOS 17 crash on dashboard load (KI-005) may corrupt in-progress user sessions. "
                "With crash rate at {:.1f}/1000 sessions and 45k+ DAU, ~135 crashes per hour. "
                "Some users report data loss post-crash.".format(crash_rate)
            ),
            "likelihood": 5 if crash_rate >= 2.5 else 4 if crash_rate >= 1.5 else 2,
            "impact": 4,
            "evidence": [
                f"Crash rate: {crash_rate}/1000 sessions (critical threshold: 2.5)",
                "KI-005: iOS 17 nil reference crash on AI Summary Widget",
                f"5 crash-related feedback entries; 1-star app store reviews appearing",
            ],
            "mitigation": (
                "Immediately disable AI Summary Widget via feature flag on iOS. "
                "Emergency patch targeting iOS 17 low-power mode edge case. "
                "Add crash analytics (Sentry) for real-time monitoring."
            ),
            "owner": "Mobile Team",
        },
        {
            "id": "R-002",
            "category": "technical",
            "title": "GraphQL N+1 query causing sustained latency degradation",
            "description": (
                "DataLoader batching under high load is falling back to N+1 queries. "
                "p95 latency currently {p95}ms (baseline: ~211ms, threshold: 300ms). "
                "Risk of cascading failure if traffic increases.".format(p95=p95)
            ),
            "likelihood": 5 if p95 >= 400 else 4 if p95 >= 300 else 2,
            "impact": 4,
            "evidence": [
                f"p95 latency: {p95}ms — 67% above baseline, breaching critical threshold",
                "KI-001: N+1 query pattern identified in pre-launch review",
                "Enterprise user reported 3× API call overhead (HAR file available)",
                "API error rate elevated at {:.2f}%".format(latest_metrics.get("error_rate", 0)),
            ],
            "mitigation": (
                "Increase DataLoader batching window. Add query complexity limits. "
                "Scale API instances horizontally. Consider reverting GraphQL dashboard "
                "queries to REST fallback endpoints temporarily."
            ),
            "owner": "Backend Platform Team",
        },
        {
            "id": "R-003",
            "category": "technical",
            "title": "Data migration corruption for complex accounts",
            "description": (
                "Migration script (KI-002, KI-007) has caused data loss for accounts "
                "with large or complex configs. Historical data >90 days missing. "
                "Risk increases as more users log in post-launch."
            ),
            "likelihood": 4,
            "impact": 5,
            "evidence": [
                "KI-007: historical data >90 days excluded from migration (DB bug)",
                "KI-002: partial migration for accounts with >500 saved configs",
                "3 support tickets reporting corrupted/missing data",
                "Data integrity feedback: 'reports showing wrong numbers'",
            ],
            "mitigation": (
                "STOP new migrations immediately until re-migration script is tested. "
                "Identify all affected accounts. Run re-migration on staging first. "
                "Communicate proactively to enterprise accounts with impact assessment."
            ),
            "owner": "Data Engineering",
        },

        # ------------------------------------------------------------------
        # BUSINESS RISKS
        # ------------------------------------------------------------------
        {
            "id": "R-004",
            "category": "business",
            "title": "Duplicate payment charges causing financial & legal exposure",
            "description": (
                "KI-006 race condition caused duplicate Stripe charges for ~0.8% of upgrades. "
                "Hotfix deployed but refund process is ongoing. "
                "Payment success rate is {:.1f}% (baseline: 98.9%). "
                "Potential chargeback risk and regulatory exposure.".format(payment_success)
            ),
            "likelihood": 3,  # hotfix deployed, but residual risk
            "impact": 5,
            "evidence": [
                f"Payment success rate: {payment_success}% (baseline 98.9%, threshold 96.5%)",
                "KI-006: duplicate charge race condition — hotfix deployed 2025-07-12",
                "2 feedback entries reporting payment failures and erroneous charges",
                "1 enterprise account threatening contract suspension",
            ],
            "mitigation": (
                "Complete refund sweep for all affected transactions within 24h. "
                "Audit Stripe webhooks for any additional duplicate events. "
                "Notify affected users proactively. Legal review of chargeback exposure. "
                "Freeze upgrade flow until full payment audit is complete."
            ),
            "owner": "Payments Team + Legal",
        },
        {
            "id": "R-005",
            "category": "business",
            "title": "Enterprise account churn and contract risk",
            "description": (
                "1 enterprise account has paused their contract. "
                "Daily churn is {churn}x baseline ({raw} cancellations/day). "
                "Enterprise users account for ~40% of ARR.".format(
                    churn=round(daily_churn / 10.3, 1), raw=daily_churn
                )
            ),
            "likelihood": 4 if daily_churn >= 30 else 3,
            "impact": 5,
            "evidence": [
                f"Daily churn: {daily_churn} cancellations (baseline: ~10, critical: 35)",
                "Enterprise customer formally paused contract (email feedback #31)",
                "3 churn-signal feedback entries from pro/enterprise tiers",
                f"D1 retention at {retention_d1}% — down from 61.8% baseline",
            ],
            "mitigation": (
                "Dedicated enterprise account manager outreach within 2h. "
                "Offer SLA credit for downtime period. Executive escalation for at-risk accounts. "
                "Public incident report with timeline and remediation plan."
            ),
            "owner": "Customer Success + Sales",
        },
        {
            "id": "R-006",
            "category": "business",
            "title": "Feature adoption target missed — business case at risk",
            "description": (
                "SmartDash 2.0 adoption funnel at 28% (target: 40% in 7 days). "
                "Combined with crashes and negative perception, organic adoption curve "
                "may be permanently stunted even after stability is restored."
            ),
            "likelihood": 4,
            "impact": 3,
            "evidence": [
                "Feature adoption funnel: 28% (target: 40%, down from 35% peak)",
                "DAU dropped below pre-launch baseline on Days 7-8",
                "Negative app store reviews may suppress organic growth",
            ],
            "mitigation": (
                "Pause adoption growth goals until stability is confirmed. "
                "Plan re-launch campaign post-stabilisation. "
                "Adjust Q3 OKR targets to reflect delay."
            ),
            "owner": "Product + Marketing",
        },

        # ------------------------------------------------------------------
        # REPUTATIONAL RISKS
        # ------------------------------------------------------------------
        {
            "id": "R-007",
            "category": "reputational",
            "title": "Negative social media momentum and app store rating damage",
            "description": (
                "Twitter complaints and 1-star app store reviews are accumulating. "
                "Support ticket volume is {tickets}x baseline. "
                "Without a public response, narrative will be set by critics.".format(
                    tickets=round(support_tickets / 31, 1)
                )
            ),
            "likelihood": 4,
            "impact": 3,
            "evidence": [
                f"Support tickets: {support_tickets}/day (baseline: ~31, critical: 120)",
                "Twitter: crash complaints, 'switching' threats",
                "App store 1-star reviews citing crashes",
                "54% negative sentiment across 35 feedback entries",
            ],
            "mitigation": (
                "Publish incident acknowledgement post within 2h. "
                "Respond to every 1-star app store review personally. "
                "Prepare media FAQ for press inquiries. "
                "CEO/CPO tweet acknowledging the issue and committing to fix."
            ),
            "owner": "Marketing/Comms + PR",
        },

        # ------------------------------------------------------------------
        # OPERATIONAL RISKS
        # ------------------------------------------------------------------
        {
            "id": "R-008",
            "category": "operational",
            "title": "Support team overwhelmed — resolution SLAs breached",
            "description": (
                "Support tickets at {tickets}/day vs baseline of ~31. "
                "Team is handling 4× normal volume. "
                "Risk of SLA breaches compounding customer dissatisfaction.".format(
                    tickets=support_tickets
                )
            ),
            "likelihood": 5 if support_tickets >= 120 else 3,
            "impact": 2,
            "evidence": [
                f"Support tickets: {support_tickets}/day (4.1× baseline)",
                "Multiple users report submitting multiple tickets without resolution",
                "Enterprise SLA is 4h response — may be breached at current volume",
            ],
            "mitigation": (
                "Activate support surge protocol — all hands on deck. "
                "Publish self-service FAQ for top 3 issues (crash, payment, data). "
                "Temporary ticket triage: prioritise enterprise, payment, and data loss. "
                "Hire 2 contract support agents for next 2 weeks."
            ),
            "owner": "Customer Success + Support Ops",
        },
    ]


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def risk_scorer() -> RiskRegister:
    """
    Score all risks and produce a ranked risk register.

    Returns:
        RiskRegister with scored risks and recommended launch posture.
    """
    latest = get_latest()
    known_issues = get_known_issues(include_post_launch=True)

    raw_risks = _build_risk_catalogue(latest, known_issues)

    risks: list[Risk] = []
    for r in raw_risks:
        likelihood = r["likelihood"]
        impact = r["impact"]
        score = likelihood * impact
        rating = (
            "critical" if score >= 20
            else "high" if score >= 12
            else "medium" if score >= 6
            else "low"
        )
        # Map score to response urgency
        response = (
            "immediate" if score >= 20
            else "24h" if score >= 12
            else "48h" if score >= 6
            else "monitor"
        )

        risks.append(Risk(
            id=r["id"],
            category=r["category"],
            title=r["title"],
            description=r["description"],
            likelihood=likelihood,
            impact=impact,
            score=score,
            rating=rating,
            evidence=r["evidence"],
            mitigation=r["mitigation"],
            owner=r["owner"],
            response=response,
        ))

    # Sort by score descending
    risks.sort(key=lambda r: -r["score"])

    # Roll-up counts
    critical_count = sum(1 for r in risks if r["rating"] == "critical")
    high_count = sum(1 for r in risks if r["rating"] == "high")
    medium_count = sum(1 for r in risks if r["rating"] == "medium")
    low_count = sum(1 for r in risks if r["rating"] == "low")

    # Category breakdown
    risk_by_category: dict[str, int] = {}
    for r in risks:
        risk_by_category[r["category"]] = risk_by_category.get(r["category"], 0) + 1

    # Recommended posture based on risk profile
    if critical_count >= 2 or any(r["id"] in ("R-003", "R-004") and r["rating"] in ("critical", "high") for r in risks):
        posture = "rollback"
        posture_rationale = (
            f"{critical_count} critical risks active including data integrity and payment exposure. "
            "Rolling back to SmartDash 1.x eliminates the attack surface while fixes are developed."
        )
    elif critical_count >= 1 or high_count >= 3:
        posture = "pause"
        posture_rationale = (
            f"{critical_count} critical and {high_count} high risks active. "
            "Pausing rollout prevents further user exposure while hot-patches are validated."
        )
    else:
        posture = "proceed"
        posture_rationale = "Risk profile is within acceptable bounds for continued rollout with monitoring."

    return RiskRegister(
        total_risks=len(risks),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        top_risks=risks[:5],
        risk_by_category=risk_by_category,
        recommended_posture=posture,
        posture_rationale=posture_rationale,
        risks=risks,
    )


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("KairosAI — risk_scorer tool")
    print("=" * 60)

    register = risk_scorer()

    print(f"\nTotal risks: {register['total_risks']}")
    print(f"  Critical: {register['critical_count']}")
    print(f"  High:     {register['high_count']}")
    print(f"  Medium:   {register['medium_count']}")
    print(f"  Low:      {register['low_count']}")
    print(f"\nRecommended posture: {register['recommended_posture'].upper()}")
    print(f"Rationale: {register['posture_rationale']}")

    print(f"\n{'ID':<8} {'Score':>6} {'Rating':>10} {'Response':>10}  Title")
    print("-" * 80)
    for r in register["risks"]:
        print(
            f"{r['id']:<8} "
            f"{r['likelihood']}×{r['impact']}={r['score']:>3}  "
            f"{r['rating']:>10} "
            f"{r['response']:>10}  "
            f"{r['title'][:45]}"
        )