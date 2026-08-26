"""Tests for Strict Binary Rubric Evaluator."""

import pytest
from content_agent.evaluator import evaluate_lesson


SAMPLE_PASSED_LESSON = """
# Introduction to RAG (Retrieval-Augmented Generation)

Imagine you are sitting for an exam.
- In a **Closed-Book Exam**, you only use what you remember in your brain. If you forget or never studied a topic, you might guess or make a mistake.
- In an **Open-Book Exam**, you can open your notebook and find the exact answer before writing it down.

**RAG is like giving an AI an Open-Book Exam!**

---

## 1. What is RAG?
RAG stands for **Retrieval-Augmented Generation**:
- **Retrieval**: Search and fetch the correct reference notes from a library or folder.
- **Augmented**: Add those notes into the prompt (the instruction message) given to the AI.
- **Generation**: Let the AI write the final answer using the fresh notes.

---

## 2. Why Do We Need RAG?
Regular AI models (called Large Language Models or LLMs, which are computer programs that understand language) have two major problems:
1. **Knowledge Cutoff**: The AI's training stopped in the past. It does not know today's news or your private company documents.
2. **Hallucination (Making up false facts)**: When the AI does not know something, it can speak with confidence but give completely wrong information!

RAG fixes this by fetching real facts first before the AI answers.

---

## 3. How RAG Works (Step-by-Step)
Here is the 4-step process:
1. **Step 1: You Ask a Question** - e.g., "What is our company's leave policy?"
2. **Step 2: Retrieve (Search)** - The system searches your company handbook and finds the exact 2 paragraphs.
3. **Step 3: Augment (Combine)** - The system combines your question + the 2 paragraphs.
4. **Step 4: Generate** - The AI reads the 2 paragraphs and writes a clean, accurate answer.

Notice: The AI model's internal weights (its underlying trained brain) are **never retrained or changed**. It simply reads the notes provided.

---

## 4. Real-World Example
Think of a Hospital Chatbot:
Without RAG, the bot might guess drug dosages.
With RAG, the bot searches the hospital's verified medicine database and gives safe, 100% verified advice.

---

## 5. Quick Practice Quiz
1. What does 'Retrieval' mean in RAG?
   - A) Retraining the whole AI model
   - B) Searching and fetching relevant reference notes
   - C) Deleting old data
   *Answer: B (Searching and fetching reference documents).*

2. Why is RAG like an open-book exam?
   - A) Because the AI can look up reference documents while answering
   - B) Because students take it online
   *Answer: A.*

3. Does RAG permanently change the AI's internal model weights?
   - A) Yes, always
   - B) No, it only reads notes in the prompt
   *Answer: B.*
"""

SAMPLE_JARGON_FLAWED_LESSON = """
# RAG Explained
RAG computes pairwise Cosine Similarity across 1536-dimensional dense vector embeddings in latent Hilbert space.
It uses an anisotropic dot-product loss function before computing token logit distributions.
"""


def test_evaluator_passes_clean_lesson():
    eval_res = evaluate_lesson(SAMPLE_PASSED_LESSON)
    assert eval_res.overall_pass is True
    assert eval_res.passed_count == 6
    assert eval_res.recommendation == "SHIP"


def test_evaluator_rejects_unexplained_jargon():
    eval_res = evaluate_lesson(SAMPLE_JARGON_FLAWED_LESSON)
    assert eval_res.overall_pass is False
    assert eval_res.checks["unexplained_jargon_guard"].passed is False
    assert eval_res.recommendation == "REVISE"
