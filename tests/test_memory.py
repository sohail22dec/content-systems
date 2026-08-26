"""Tests for Persistent Long-Term Memory and Rule Evolution."""

import os
import tempfile
from pathlib import Path
import pytest
from content_agent.memory import AgentMemoryStore


def test_memory_store_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_memory.db"
        store = AgentMemoryStore(db_path=test_db_path)

        # Verify default rules were seeded
        rules = store.get_active_rules(limit=5)
        assert len(rules) > 0

        # Record a run with rejection
        run_id = store.record_run(
            topic="Introduction to RAG",
            status="PASSED",
            total_iterations=2,
            final_draft="# Lesson Content",
            eval_report={"overall_pass": True},
            rejection_logs=[{
                "iteration": 0,
                "failed_checkpoints": ["unexplained_jargon_guard"],
                "diagnostics": [{
                    "checkpoint": "unexplained_jargon_guard",
                    "reasoning": "Dense math terms used",
                    "remediation": "Translate all math terms to plain language.",
                }],
                "strategy_applied": "Surgical fix on jargon",
            }]
        )
        assert run_id > 0

        # Verify active rules updated
        active = store.get_active_rules(limit=10)
        assert any("plain language" in r.lower() for r in active)
