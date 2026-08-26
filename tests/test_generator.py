"""Tests for Pedagogical Generator Node."""

import pytest
from content_agent.generator import generate_lesson_draft


def test_generator_produces_lesson():
    topic = "Introduction to RAG (Retrieval-Augmented Generation)"
    draft = generate_lesson_draft(topic=topic)
    assert draft is not None
    assert len(draft) > 200
    assert "RAG" in draft or "Retrieval" in draft
