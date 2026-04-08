"""
KairosAI — JSON Writer
------------------------
Writes the final decision dict to a structured JSON file in reports/.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def write_json_report(decision: dict, reports_dir: str = "reports") -> str:
    """
    Persist the final decision as a JSON file.

    Args:
        decision    : the full decision dict from Orchestrator.run()
        reports_dir : directory to write into (created if missing)

    Returns:
        Path to the written file as a string.
    """
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session_id = decision.get("meta", {}).get("session_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"warroom_{session_id}_{ts}.json"
    filepath = out_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2, ensure_ascii=False)

    return str(filepath)