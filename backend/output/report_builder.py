"""
KairosAI — Report Builder
---------------------------
Assembles the final war room package:
  - JSON decision file
  - Markdown human report
  - Console summary print
"""

from .json_writer import write_json_report
from .markdown_writer import write_markdown_report


def build_report(decision: dict, reports_dir: str = "reports") -> dict:
    """
    Write all report formats and return a summary of what was written.

    Args:
        decision    : the full decision dict from Orchestrator.run()
        reports_dir : output directory

    Returns:
        dict with paths to all written files.
    """
    json_path = write_json_report(decision, reports_dir)
    md_path   = write_markdown_report(decision, reports_dir)

    return {
        "json_report":     json_path,
        "markdown_report": md_path,
        "session_id":      decision.get("meta", {}).get("session_id", "unknown"),
        "verdict":         decision.get("decision", "UNKNOWN"),
        "confidence":      decision.get("confidence", {}).get("weighted_score", 0),
    }