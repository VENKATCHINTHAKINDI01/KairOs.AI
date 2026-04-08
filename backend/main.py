"""
KairosAI — main.py
--------------------
Entry point for the war room CLI.
LLM backend: Groq (free — get key at console.groq.com)

Usage:
    python main.py                    # run full war room
    python main.py --dry-run          # validate imports + tools, no API calls
    python main.py --monitor "..."    # ask monitor a question after the run
    python main.py --json-only        # print final JSON to stdout

Environment (.env):
    GROQ_API_KEY=gsk_...
    GROQ_MODEL=llama-3.3-70b-versatile   (optional, this is the default)
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Env check
# ---------------------------------------------------------------------------

def check_env():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your_groq_api_key_here":
        print("\n[ERROR] GROQ_API_KEY is not set.")
        print("  1. Go to console.groq.com → API Keys → Create API Key")
        print("  2. Copy the key (starts with gsk_...)")
        print("  3. Add to your .env file:  GROQ_API_KEY=gsk_...\n")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Dry run — no API calls
# ---------------------------------------------------------------------------

def dry_run():
    print("\nKairosAI — Dry Run (import + tools validation)\n")

    print("[1/3] Data layer...")
    from data.metrics import get_all, get_baseline, KPI_THRESHOLDS
    from data.feedback import get_all as get_feedback, get_summary_stats
    from data.release_notes import get_known_issues, get_success_criteria
    stats = get_summary_stats()
    print(f"  ✅ metrics  : {len(get_all())} days  (baseline: {len(get_baseline())})")
    print(f"  ✅ feedback : {stats['total']} entries — {stats['negative_pct']}% negative")
    print(f"  ✅ issues   : {len(get_known_issues())} known issues")

    print("\n[2/3] Tools layer...")
    from tools.aggregate_metrics  import aggregate_metrics
    from tools.detect_anomalies   import detect_anomalies
    from tools.sentiment_analyzer import sentiment_analyzer
    from tools.trend_compare      import trend_compare
    from tools.risk_scorer        import risk_scorer

    agg  = aggregate_metrics()
    anom = detect_anomalies()
    sent = sentiment_analyzer()
    trnd = trend_compare()
    risk = risk_scorer()

    print(f"  ✅ aggregate_metrics  → health={agg['overall_health']}  "
          f"CRIT={agg['critical_count']}  WARN={agg['warn_count']}")
    print(f"  ✅ detect_anomalies   → {anom['total_anomalies']} anomalies  "
          f"{anom['high_severity']} high-severity")
    print(f"  ✅ sentiment_analyzer → score={sent['overall_score']}  "
          f"dominant={sent['dominant_sentiment']}")
    print(f"  ✅ trend_compare      → verdict={trnd['launch_impact_verdict']}  "
          f"worst_kpi={trnd['worst_kpi']}")
    print(f"  ✅ risk_scorer        → {risk['total_risks']} risks  "
          f"posture={risk['recommended_posture']}")

    print("\n[3/3] Agents + Core layer...")
    from agents import (PMAgent, AnalystAgent, MarketingAgent,
                        RiskAgent, SREAgent, MonitorAgent, ModeratorAgent)
    for AgentClass in [PMAgent, AnalystAgent, MarketingAgent,
                       RiskAgent, SREAgent]:
        a = AgentClass()
        print(f"  ✅ {a.name:<25} tools={a.tools_to_use}")

    m = MonitorAgent()
    mod = ModeratorAgent()
    print(f"  ✅ {m.name:<25} (session memory)")
    print(f"  ✅ {mod.name:<25} (runs after all agents)")

    from core.orchestrator import Orchestrator
    orch = Orchestrator()
    print(f"  ✅ Orchestrator        session={orch.session_id}")

    print("\n" + "═" * 52)
    print("  All systems GO.")
    print("  Run:  python main.py")
    print("═" * 52 + "\n")


# ---------------------------------------------------------------------------
# Full war room run
# ---------------------------------------------------------------------------

def run_war_room(monitor_question: str | None = None) -> dict:
    check_env()

    from core.orchestrator    import Orchestrator
    from output.report_builder import build_report
    from output.trace_logger   import TraceLogger

    orch   = Orchestrator()
    logger = TraceLogger(orch.session_id)

    logger.session_start("PurpleMerit — SmartDash 2.0")

    decision = orch.run()

    logger.final_decision(
        verdict         = decision["decision"],
        confidence      = decision["confidence"]["weighted_score"],
        score_breakdown = decision["confidence"],
    )
    logger.risk_register(decision.get("risk_register", []))
    logger.action_plan(decision.get("action_plan", {}))

    report_paths = build_report(decision)
    logger.session_end(report_paths["json_report"])

    if monitor_question:
        print(f"\n{'─'*52}")
        print(f"  War Room Monitor — Q&A")
        print(f"{'─'*52}")
        print(f"  Q: {monitor_question}")
        answer = orch.monitor.answer(monitor_question)
        print(f"\n  A:\n{answer}\n")

    print(f"\n  Reports written:")
    print(f"    JSON : {report_paths['json_report']}")
    print(f"    MD   : {report_paths['markdown_report']}\n")

    return decision


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="KairosAI — Multi-Agent Product Launch War Room (powered by Groq)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate all imports and tools without making any API calls",
    )
    parser.add_argument(
        "--monitor", type=str, default=None, metavar="QUESTION",
        help='Ask the Monitor after the run. E.g. --monitor "What did Risk say?"',
    )
    parser.add_argument(
        "--json-only", action="store_true",
        help="Print the final decision JSON to stdout after the run",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Start the FastAPI + WebSocket API server",
    )

    args = parser.parse_args()

    if args.serve:
        serve()
        return

    if args.dry_run:
        dry_run()
        return

    decision = run_war_room(monitor_question=args.monitor)

    if args.json_only:
        print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# API server mode (added below existing main())
# ---------------------------------------------------------------------------

def serve():
    """Start the FastAPI + WebSocket server."""
    import uvicorn
    check_env()
    print("\nKairosAI API server starting...")
    print("  Docs  : http://localhost:8000/docs")
    print("  WS    : ws://localhost:8000/api/v1/warroom/stream")
    print("  Health: http://localhost:8000/health\n")
    uvicorn.run(
        "api.app:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True,
        log_level="info",
    )