"""Diagnostician Node for analyzing rejections and formulating targeted repair instructions."""

from datetime import datetime
from typing import Dict, Any, List, Tuple
from content_agent.state import RubricEvaluation, RejectionRecord


def diagnose_rejection(
    eval_report: RubricEvaluation,
    iteration: int
) -> Tuple[RejectionRecord, str]:
    """Analyze failed rubric checkpoints and formulate a surgical revision strategy.

    Args:
        eval_report: The RubricEvaluation containing checkpoint statuses and diagnostics.
        iteration: The current iteration index.

    Returns:
        Tuple of (RejectionRecord, revision_instructions_string).
    """
    failed_checkpoints: List[str] = []
    diagnostics: List[Dict[str, Any]] = []
    repair_bullets: List[str] = []

    for name, check in eval_report.checks.items():
        if not check.passed:
            failed_checkpoints.append(name)
            diag_entry = {
                "checkpoint": name,
                "title": check.title,
                "reasoning": check.reasoning,
                "offending_snippet": check.offending_snippet,
                "remediation": check.remediation_instruction,
            }
            diagnostics.append(diag_entry)

            bullet = f"- **{check.title} (FAILED)**: {check.reasoning}"
            if check.offending_snippet:
                bullet += f"\n  - *Problematic snippet found*: \"{check.offending_snippet}\""
            if check.remediation_instruction:
                bullet += f"\n  - *Required fix*: {check.remediation_instruction}"
            repair_bullets.append(bullet)

    strategy_text = (
        f"Iterative Surgical Repair (Iteration {iteration + 1}): Addressing {len(failed_checkpoints)} "
        f"failed checkpoint(s): {', '.join(failed_checkpoints)}. "
        f"Preserving all valid pedagogical structure while surgically replacing offending passages."
    )

    rejection_record = RejectionRecord(
        iteration=iteration,
        timestamp=datetime.now().isoformat(),
        failed_checkpoints=failed_checkpoints,
        diagnostics=diagnostics,
        strategy_applied=strategy_text
    )

    revision_instructions = (
        "### ⚠️ REVISION REQUIRED - STRICT QUALITY AUDIT FAILED\n"
        "Your previous draft was rejected by the Chief Evaluator. "
        "You must surgically correct the following issues on this retry:\n\n"
        + "\n\n".join(repair_bullets)
        + "\n\n"
        "### MANDATORY REVISION RULES:\n"
        "1. DO NOT change parts of the lesson that already passed (e.g. good analogies or clean formatting).\n"
        "2. Directly address each of the required fixes above.\n"
        "3. Ensure the revised draft is 100% complete and standalone (do not output diffs or partial text).\n"
        "4. Remember the student is a 12th grader from India with limited English vocabulary."
    )

    return rejection_record, revision_instructions
