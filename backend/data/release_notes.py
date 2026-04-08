"""
KairosAI — Release Notes & Known Issues
-----------------------------------------
Describes the PurpleMerit "SmartDash 2.0" feature launch.
Used by agents to understand what changed and what risks were pre-identified.
"""


RELEASE_NOTES: dict = {
    "release_id": "PM-2025-07-07",
    "product": "PurpleMerit",
    "feature_name": "SmartDash 2.0",
    "release_date": "2025-07-07",
    "release_type": "major_feature",
    "rollout_strategy": "full_release",      # was supposed to be gradual, changed last-minute

    # -----------------------------------------------------------------
    # What changed
    # -----------------------------------------------------------------
    "summary": (
        "SmartDash 2.0 is a full redesign of PurpleMerit's analytics dashboard. "
        "It introduces real-time AI-powered summaries, collaborative annotation layers, "
        "a new data visualisation engine (migrated from D3 v6 to v7), and "
        "a redesigned settings panel. All existing dashboard configurations are "
        "auto-migrated on first login. The underlying API now uses GraphQL for "
        "dashboard queries, replacing the legacy REST endpoints which remain "
        "available for 90 days as a fallback."
    ),

    "key_changes": [
        {
            "change": "AI Summary Widget",
            "description": "GPT-4-powered summary panel auto-generates insights from your data at dashboard load.",
            "risk_level": "medium",
            "notes": "Adds ~200ms latency on load due to LLM call. Cached after first render per session.",
        },
        {
            "change": "GraphQL API Migration",
            "description": "Dashboard data layer migrated from REST to GraphQL. Legacy REST endpoints available as fallback.",
            "risk_level": "high",
            "notes": (
                "N+1 query risk identified in code review. Mitigation: DataLoader batching added. "
                "Under high concurrency, batching may not fully compensate — needs monitoring."
            ),
        },
        {
            "change": "D3 v7 Upgrade",
            "description": "Charting library upgraded from D3 v6 to v7. Breaking API changes handled via shim layer.",
            "risk_level": "medium",
            "notes": "Shim tested on 80% of chart types. Edge-case chart configs may render incorrectly.",
        },
        {
            "change": "Auto-Migration of Dashboard Configs",
            "description": "First login after update triggers a background migration of user's saved dashboard layouts.",
            "risk_level": "high",
            "notes": (
                "Migration script tested on sample of 5k accounts. "
                "Complex configs (nested filters, custom date ranges) may migrate incorrectly. "
                "Manual rollback available via support."
            ),
        },
        {
            "change": "Collaborative Annotation Layer",
            "description": "Teams can now pin notes and comments directly on chart data points.",
            "risk_level": "low",
            "notes": "Requires WebSocket connection. May fail silently on restrictive corporate firewalls.",
        },
        {
            "change": "New Settings Panel",
            "description": "Settings restructured into tabbed layout. Billing and team management relocated.",
            "risk_level": "low",
            "notes": "User navigation patterns expected to require adjustment period.",
        },
    ],

    # -----------------------------------------------------------------
    # Pre-known issues (documented before launch)
    # -----------------------------------------------------------------
    "known_issues_pre_launch": [
        {
            "id": "KI-001",
            "severity": "high",
            "component": "GraphQL / DataLoader",
            "description": (
                "Under sustained concurrent load (>500 simultaneous dashboard loads), "
                "the DataLoader batching window may be exceeded, causing N+1 query fallback. "
                "This results in 3-5× query overhead and latency spikes."
            ),
            "status": "accepted_risk",
            "mitigation": "Rollback to REST if p95 latency exceeds 350ms. Alert threshold set.",
            "owner": "Backend Platform Team",
        },
        {
            "id": "KI-002",
            "severity": "medium",
            "component": "Auto-Migration Script",
            "description": (
                "Migration script for accounts with >500 saved dashboard configs may "
                "time out on the first login, causing a partial migration. "
                "Affected accounts see blank dashboard panels until migration completes."
            ),
            "status": "known_bug",
            "mitigation": "Retry logic added. Support team briefed for manual resolution.",
            "owner": "Data Engineering",
        },
        {
            "id": "KI-003",
            "severity": "medium",
            "component": "Payment Flow",
            "description": (
                "The settings panel redesign relocated the billing section. "
                "A routing bug (PR #2841) was merged but not fully tested — "
                "users upgrading via the in-app CTA may hit a 404 before being redirected. "
                "Second attempt succeeds."
            ),
            "status": "known_bug",
            "mitigation": "Fix targeted for next patch (ETA: 72 hours post-launch).",
            "owner": "Frontend Team",
        },
        {
            "id": "KI-004",
            "severity": "low",
            "component": "D3 v7 Shim",
            "description": "Custom polar chart configurations (used by ~2% of users) may render with misaligned axes.",
            "status": "known_bug",
            "mitigation": "Users can switch to the legacy chart engine from settings.",
            "owner": "Visualisation Team",
        },
    ],

    # -----------------------------------------------------------------
    # Issues discovered POST-launch (added as they emerged)
    # -----------------------------------------------------------------
    "known_issues_post_launch": [
        {
            "id": "KI-005",
            "severity": "critical",
            "component": "iOS App / Dashboard Load",
            "discovered": "2025-07-10",
            "description": (
                "iOS 17 app crashes when the AI Summary Widget attempts to render "
                "while the device is in low-power mode. The crash is triggered by "
                "an unhandled nil reference in the Swift WebView bridge."
            ),
            "status": "in_progress",
            "mitigation": "Hot-patch in review. Workaround: disable low-power mode.",
            "owner": "Mobile Team",
        },
        {
            "id": "KI-006",
            "severity": "critical",
            "component": "Payment Gateway",
            "discovered": "2025-07-11",
            "description": (
                "KI-003 routing bug has a more severe consequence than initially assessed: "
                "under certain race conditions, payment events are sent twice to Stripe, "
                "resulting in duplicate charges. Affects ~0.8% of upgrade transactions."
            ),
            "status": "hotfix_deployed",
            "mitigation": "Hotfix deployed 2025-07-12 18:00 UTC. Refund process initiated for affected users.",
            "owner": "Frontend Team + Payments Team",
        },
        {
            "id": "KI-007",
            "severity": "high",
            "component": "Data Migration",
            "discovered": "2025-07-11",
            "description": (
                "For accounts migrated from the legacy dashboard, "
                "historical data older than 90 days is not included in the migration. "
                "The migration script incorrectly treated the REST fallback window (90 days) "
                "as a data retention window."
            ),
            "status": "investigating",
            "mitigation": "Legacy data still exists in DB. Re-migration script being tested.",
            "owner": "Data Engineering",
        },
    ],

    # -----------------------------------------------------------------
    # Rollout metadata
    # -----------------------------------------------------------------
    "rollout_details": {
        "planned_strategy": "10%_canary_then_gradual",
        "actual_strategy": "full_release",
        "reason_for_change": (
            "Marketing campaign was pre-announced to press with the launch date. "
            "Product leadership decided to go full release to match announcement."
        ),
        "rollback_procedure": (
            "1. Toggle feature flag SMARTDASH_V2 to OFF in LaunchDarkly. "
            "2. Users will revert to SmartDash 1.x automatically. "
            "3. GraphQL endpoint can remain live for API consumers. "
            "4. Migration data is preserved — re-migration can be attempted later. "
            "Estimated rollback time: 15 minutes."
        ),
        "rollback_risk": "Low — feature flag rollback is tested and non-destructive.",
        "data_risk_on_rollback": "Medium — users who modified data in SmartDash 2.0 may see stale views in 1.x.",
    },

    # -----------------------------------------------------------------
    # Success criteria (as defined by PM pre-launch)
    # -----------------------------------------------------------------
    "success_criteria": {
        "must_have": [
            "Crash rate stays below 2.0 per 1000 sessions (currently: 2.4 — BREACHED)",
            "p95 latency stays below 300ms (currently: 352ms — BREACHED)",
            "Payment success rate stays above 97% (currently: 96.7% — BORDERLINE)",
            "D1 retention does not drop more than 5pp from baseline (dropped 5.5pp — BREACHED)",
        ],
        "nice_to_have": [
            "Feature adoption funnel reaches 40% within 7 days (currently: 28% — MISSED)",
            "Support ticket volume normalises within 5 days (still elevated — MISSED)",
        ],
        "current_verdict": "2 of 4 must-have criteria are currently breached.",
    },
}


def get_all() -> dict:
    """Return the full release notes dict."""
    return RELEASE_NOTES


def get_known_issues(include_post_launch: bool = True) -> list[dict]:
    """Return all known issues, optionally including post-launch discoveries."""
    issues = RELEASE_NOTES["known_issues_pre_launch"].copy()
    if include_post_launch:
        issues.extend(RELEASE_NOTES["known_issues_post_launch"])
    return issues


def get_critical_issues() -> list[dict]:
    """Return only critical severity issues."""
    return [i for i in get_known_issues() if i["severity"] == "critical"]


def get_success_criteria() -> dict:
    """Return the PM-defined success criteria."""
    return RELEASE_NOTES["success_criteria"]


def get_rollback_info() -> dict:
    """Return rollback procedure details."""
    return RELEASE_NOTES["rollout_details"]


if __name__ == "__main__":
    import json
    print(f"Feature: {RELEASE_NOTES['feature_name']}")
    print(f"Release date: {RELEASE_NOTES['release_date']}")
    print(f"\nTotal known issues: {len(get_known_issues())}")
    print(f"Critical issues: {len(get_critical_issues())}")
    print("\nSuccess criteria verdict:")
    print(RELEASE_NOTES["success_criteria"]["current_verdict"])
    print("\nCritical issues:")
    for issue in get_critical_issues():
        print(f"  [{issue['id']}] {issue['component']}: {issue['description'][:80]}...")

    