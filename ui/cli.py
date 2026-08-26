"""Command Line Interface for Content Systems Agent."""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from content_agent.graph import run_content_pipeline
from content_agent.memory import memory_store
from content_agent.error_injector import DELIBERATE_ERROR_TYPES
from content_agent.config import (
    PASSED_LESSON_PATH,
    REJECTION_LOG_PATH,
    EVOLVED_RULES_PATH,
)

console = Console()


def print_banner():
    banner = Text(
        "🚀 Content Systems: Autonomous Self-Evaluating Lesson Generator\n"
        "Target Persona: 12th-Grade Graduate (India, Non-English Medium, Beginner)",
        style="bold cyan",
        justify="center",
    )
    console.print(Panel(banner, border_style="cyan"))


def list_rules():
    rules = memory_store.export_evolved_rules_json()
    table = Table(title="🧠 Evolved Memory Rules (Persistent Cross-Run Learning)", header_style="bold magenta")
    table.add_column("Rule ID", style="cyan")
    table.add_column("Pattern Detected", style="yellow")
    table.add_column("Learned Instruction", style="green")
    table.add_column("Occurrences", justify="center", style="bold")

    for r in rules.get("evolved_rules", []):
        table.add_row(r["rule_id"], r["pattern"][:60] + "...", r["instruction"], str(r["occurrences"]))

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="Run Autonomous Self-Evaluating Lesson Content Generator."
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Introduction to RAG (Retrieval-Augmented Generation)",
        help="The lesson topic to generate",
    )
    parser.add_argument(
        "--inject-error",
        type=str,
        choices=list(DELIBERATE_ERROR_TYPES.keys()),
        default=None,
        help="Inject a deliberate fault into Draft 1 to demonstrate evaluator detection & self-correction",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum regeneration retries before terminating",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="Display persistent evolved memory rules",
    )

    args = parser.parse_args()

    if args.list_rules:
        list_rules()
        sys.exit(0)

    print_banner()

    console.print(f"[bold green]Topic:[/bold green] {args.topic}")
    if args.inject_error:
        error_info = DELIBERATE_ERROR_TYPES[args.inject_error]
        console.print(
            f"[bold red]⚠️ Deliberate Error Injected (for Demo):[/bold red] "
            f"{error_info['label']} ({error_info['description']})"
        )
    else:
        console.print("[dim]Standard generation mode (No deliberate faults injected)[/dim]")

    console.print("\n[bold cyan]Starting LangGraph Agentic Pipeline...[/bold cyan]\n")

    with console.status("[bold green]Executing agentic graph...[/bold green]", spinner="dots"):
        result = run_content_pipeline(
            topic=args.topic,
            deliberate_error=args.inject_error,
            max_retries=args.max_retries,
        )

    final_status = result.get("final_status")
    total_drafts = len(result.get("draft_history", []))
    rejections = result.get("rejection_log", [])

    console.print("\n" + "=" * 60 + "\n")
    if final_status == "PASSED":
        console.print(
            Panel(
                f"[bold green]✓ SUCCESS: Lesson cleared all strict binary rubric gates![/bold green]\n"
                f"Total Drafts: {total_drafts} | Total Rejections Handled: {len(rejections)}\n\n"
                f"📄 Passed Lesson Saved: [bold cyan]{PASSED_LESSON_PATH}[/bold cyan]\n"
                f"📊 Rejection Audit Log: [bold yellow]{REJECTION_LOG_PATH}[/bold yellow]\n"
                f"🧠 Evolved Memory DB: [bold magenta]{EVOLVED_RULES_PATH}[/bold magenta]",
                title="🏆 Run Completed",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]✗ FAILED: Reached maximum retries without clearing all checkpoints.[/bold red]\n"
                f"Total Drafts: {total_drafts} | Rejections: {len(rejections)}\n\n"
                f"📊 Rejection Audit Log: [bold yellow]{REJECTION_LOG_PATH}[/bold yellow]",
                title="⚠️ Run Terminated",
                border_style="red",
            )
        )


if __name__ == "__main__":
    main()
