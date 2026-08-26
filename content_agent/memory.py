"""Persistent Long-Term Memory & Self-Evolving Rule Synthesizer for Content Systems."""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from content_agent.config import DB_PATH, EVOLVED_RULES_PATH
from content_agent.state import EvolvedRule


class AgentMemoryStore:
    """Persistent SQLite and JSON memory manager that tracks runs and synthesizes rules across executions."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite tables for runs, rejections, and evolved rules."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Table for full agent execution runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_iterations INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    final_draft TEXT,
                    evaluation_json TEXT
                )
            """)
            # Table for granular rejection events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rejections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    iteration INTEGER NOT NULL,
                    failed_checkpoints TEXT NOT NULL,
                    diagnostics_json TEXT NOT NULL,
                    strategy_applied TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                )
            """)
            # Table for self-evolved guidelines
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evolved_rules (
                    rule_id TEXT PRIMARY KEY,
                    pattern TEXT NOT NULL,
                    rule_instruction TEXT NOT NULL,
                    occurrences INTEGER DEFAULT 1,
                    last_observed TEXT NOT NULL
                )
            """)
            conn.commit()

        # Seed initial core rules if table is empty
        self._seed_default_rules()

    def _seed_default_rules(self):
        """Seed initial high-priority pedagogical constraints."""
        default_rules = [
            (
                "rule_analogy_first",
                "Abstract technical definitions without an introductory concrete metaphor cause student confusion.",
                "Always introduce an intuitive everyday analogy (e.g. open-book vs closed-book exam) in the first 2 sections before any technical terms.",
                3,
                datetime.now().isoformat()
            ),
            (
                "rule_zero_math_jargon",
                "Using terms like 'Cosine Similarity', 'Latent Hilbert Space', or 'Vector Dimension' alienates 12th-grade beginners.",
                "Never use advanced linear algebra or mathematical vector formulas. Explain matching simply as 'finding the most relevant reference note card'.",
                4,
                datetime.now().isoformat()
            ),
            (
                "rule_mandatory_why_section",
                "Skipping the explanation of LLM knowledge cutoffs and hallucinations weakens the motivation for RAG.",
                "Always include a dedicated 'Why RAG is Needed' section highlighting that AI without RAG can invent false facts or has outdated memory.",
                2,
                datetime.now().isoformat()
            ),
        ]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for r_id, pat, inst, occ, ts in default_rules:
                cursor.execute("""
                    INSERT OR IGNORE INTO evolved_rules (rule_id, pattern, rule_instruction, occurrences, last_observed)
                    VALUES (?, ?, ?, ?, ?)
                """, (r_id, pat, inst, occ, ts))
            conn.commit()

    def record_run(
        self,
        topic: str,
        status: str,
        total_iterations: int,
        final_draft: str,
        eval_report: Optional[Dict[str, Any]],
        rejection_logs: List[Dict[str, Any]]
    ) -> int:
        """Save a complete pipeline execution trace to memory."""
        now = datetime.now().isoformat()
        eval_json_str = json.dumps(eval_report) if eval_report else "{}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (topic, status, total_iterations, created_at, final_draft, evaluation_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (topic, status, total_iterations, now, final_draft, eval_json_str))
            run_id = cursor.lastrowid

            for rec in rejection_logs:
                cursor.execute("""
                    INSERT INTO rejections (run_id, iteration, failed_checkpoints, diagnostics_json, strategy_applied, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    rec.get("iteration", 0),
                    json.dumps(rec.get("failed_checkpoints", [])),
                    json.dumps(rec.get("diagnostics", [])),
                    rec.get("strategy_applied", ""),
                    rec.get("timestamp", now)
                ))

            conn.commit()

        # Evolve rules based on any new rejections recorded
        if rejection_logs:
            self._evolve_rules_from_rejections(rejection_logs)

        # Export updated rules to JSON artifact
        self.export_evolved_rules_json()
        return run_id

    def _evolve_rules_from_rejections(self, rejection_logs: List[Dict[str, Any]]):
        """Analyze rejection logs and synthesize or increment learned prompt rules."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for log in rejection_logs:
                for diag in log.get("diagnostics", []):
                    chk = diag.get("checkpoint", "")
                    rem = diag.get("remediation", "")
                    reason = diag.get("reasoning", "")
                    if not chk or not rem:
                        continue

                    rule_id = f"evolved_{chk}"
                    # Check if rule exists
                    cursor.execute("SELECT occurrences FROM evolved_rules WHERE rule_id = ?", (rule_id,))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute("""
                            UPDATE evolved_rules
                            SET occurrences = occurrences + 1, last_observed = ?, rule_instruction = ?
                            WHERE rule_id = ?
                        """, (now, rem, rule_id))
                    else:
                        cursor.execute("""
                            INSERT INTO evolved_rules (rule_id, pattern, rule_instruction, occurrences, last_observed)
                            VALUES (?, ?, ?, 1, ?)
                        """, (rule_id, reason[:200], rem, now))
            conn.commit()

    def get_active_rules(self, limit: int = 5) -> List[str]:
        """Fetch the highest-priority evolved rules ordered by occurrence frequency."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rule_instruction FROM evolved_rules
                ORDER BY occurrences DESC, last_observed DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def export_evolved_rules_json(self) -> Dict[str, Any]:
        """Export all evolved rules to the outputs/evolved_rules.json file for auditability."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rule_id, pattern, rule_instruction, occurrences, last_observed
                FROM evolved_rules
                ORDER BY occurrences DESC
            """)
            rows = cursor.fetchall()

        rules_data = []
        for r_id, pat, inst, occ, ts in rows:
            rules_data.append({
                "rule_id": r_id,
                "pattern": pat,
                "instruction": inst,
                "occurrences": occ,
                "last_observed": ts
            })

        output_payload = {
            "total_rules": len(rules_data),
            "generated_at": datetime.now().isoformat(),
            "evolved_rules": rules_data
        }

        with open(EVOLVED_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

        return output_payload


# Singleton memory instance
memory_store = AgentMemoryStore()
