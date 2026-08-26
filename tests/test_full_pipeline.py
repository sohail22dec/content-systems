"""End-to-End Pipeline Integration Tests for LangGraph Workflow."""

import pytest
from content_agent.graph import run_content_pipeline
from content_agent.config import PASSED_LESSON_PATH, REJECTION_LOG_PATH


def test_pipeline_normal_run():
    """Test standard pipeline run where content passes rubric."""
    result = run_content_pipeline(
        topic="Introduction to RAG (Retrieval-Augmented Generation)",
        deliberate_error=None,
        max_retries=2,
    )
    assert result["final_status"] == "PASSED"
    assert len(result["draft_history"]) >= 1
    assert result["current_draft"] is not None
    assert PASSED_LESSON_PATH.exists()


def test_pipeline_deliberate_error_self_correction():
    """Test pipeline catches deliberate error on draft 1 and self-corrects to PASS on draft 2."""
    result = run_content_pipeline(
        topic="Introduction to RAG (Retrieval-Augmented Generation)",
        deliberate_error="unexplained_jargon",
        max_retries=2,
    )
    # Total drafts should be at least 2 (Draft 1 failed -> Diagnosed -> Draft 2 passed)
    assert len(result["draft_history"]) >= 2
    assert len(result["rejection_log"]) >= 1
    assert result["final_status"] == "PASSED"
    
    # Check that Draft 1 had the jargon and Draft 2 cleaned it up
    d1 = result["draft_history"][0]["content"]
    d_final = result["current_draft"]
    assert "Cosine Similarity" in d1
    assert "Cosine Similarity" not in d_final
