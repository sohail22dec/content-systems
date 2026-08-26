"""Audit Logging & Artifact Generation Module for Content Systems."""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from content_agent.config import (
    PASSED_LESSON_PATH,
    REJECTION_LOG_PATH,
    EVOLVED_RULES_PATH,
    OUTPUTS_DIR,
)
from content_agent.state import RubricEvaluation

console = Console()


def save_lesson_artifact(draft: str, filename: Optional[str] = None) -> Path:
    """Save the final passing lesson content to markdown artifact."""
    target_path = OUTPUTS_DIR / filename if filename else PASSED_LESSON_PATH
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(draft)
    return target_path


def save_rejection_log_artifact(rejection_logs: List[Dict[str, Any]], topic: str, final_status: str) -> Path:
    """Save the structured rejection log to outputs/rejection_log.json."""
    payload = {
        "topic": topic,
        "final_status": final_status,
        "timestamp": datetime.now().isoformat(),
        "total_rejections": len(rejection_logs),
        "rejection_history": rejection_logs,
    }
    with open(REJECTION_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return REJECTION_LOG_PATH


def print_evaluation_scorecard(eval_report: RubricEvaluation, iteration: int):
    """Render a clean, colorful Rich terminal scorecard for the rubric evaluation."""
    status_style = "bold green" if eval_report.overall_pass else "bold red"
    status_text = "PASSED (SHIP)" if eval_report.overall_pass else "REJECTED (REVISE)"

    table = Table(
        title=f"📋 Rubric Scorecard — Iteration {iteration + 1} [{status_text}]",
        title_style=status_style,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Checkpoint", style="bold", width=26)
    table.add_column("Result", justify="center", width=10)
    table.add_column("Reasoning & Feedback", style="dim")

    for key, check in eval_report.checks.items():
        res_str = "[green]✓ PASS[/green]" if check.passed else "[red]✗ FAIL[/red]"
        feedback = check.reasoning
        if not check.passed and check.offending_snippet:
            feedback += f"\n[yellow]Offending Quote: \"{check.offending_snippet}\"[/yellow]"
        table.add_row(check.title, res_str, feedback)

    console.print(table)
    console.print(
        Panel(
            f"[bold]Summary:[/bold] {eval_report.summary}\n"
            f"[bold]Recommendation:[/bold] [{status_style}]{eval_report.recommendation}[/{status_style}] "
            f"({eval_report.passed_count}/{eval_report.total_count} passed)",
            border_style="green" if eval_report.overall_pass else "red",
        )
    )
