"""Tests for Deliberate Error Injection & Self-Correction Evaluation."""

import pytest
from content_agent.error_injector import inject_deliberate_error
from content_agent.evaluator import evaluate_lesson
from tests.test_evaluator import SAMPLE_PASSED_LESSON


def test_unexplained_jargon_injection():
    corrupted = inject_deliberate_error(SAMPLE_PASSED_LESSON, "unexplained_jargon")
    assert "Cosine Similarity" in corrupted
    eval_res = evaluate_lesson(corrupted)
    assert eval_res.overall_pass is False
    assert eval_res.checks["unexplained_jargon_guard"].passed is False


def test_dense_vocabulary_injection():
    corrupted = inject_deliberate_error(SAMPLE_PASSED_LESSON, "dense_vocabulary")
    assert "Epistemological" in corrupted or "epistemologically" in corrupted
    eval_res = evaluate_lesson(corrupted)
    assert eval_res.overall_pass is False
    assert eval_res.checks["vocabulary_accessibility"].passed is False


def test_factual_error_injection():
    corrupted = inject_deliberate_error(SAMPLE_PASSED_LESSON, "factual_error")
    assert "retrains and updates the neural weights" in corrupted
    eval_res = evaluate_lesson(corrupted)
    assert eval_res.overall_pass is False
    assert eval_res.checks["grounded_accuracy"].passed is False
