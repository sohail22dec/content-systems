"""Deliberate Error Injector Module for Loom Video Demonstration and Pipeline Robustness Testing."""

import re


DELIBERATE_ERROR_TYPES = {
    "unexplained_jargon": {
        "label": "Unexplained Math & Vector Jargon",
        "description": "Injects dense mathematical and vector embedding jargon without explanation into Section 3.",
    },
    "missing_why": {
        "label": "Missing Motivation & Hallucination Section",
        "description": "Strips out the fundamental 'Why is RAG needed' and LLM knowledge cutoff explanation.",
    },
    "dense_vocabulary": {
        "label": "Dense Academic & High-Syllable Vocabulary",
        "description": "Replaces beginner-friendly words with complex academic prose unsuitable for 12th-grade non-English learners.",
    },
    "factual_error": {
        "label": "Factual Hallucination (Weight Retraining Claim)",
        "description": "Injects a false claim that RAG permanently updates and retrains the neural network weights.",
    },
}


def inject_deliberate_error(draft: str, error_type: str) -> str:
    """Inject a targeted deliberate fault into the draft content for demonstration purposes.

    Args:
        draft: The generated lesson markdown text.
        error_type: Key from DELIBERATE_ERROR_TYPES.

    Returns:
        Corrupted draft string containing the deliberate fault.
    """
    if not error_type or error_type not in DELIBERATE_ERROR_TYPES:
        return draft

    corrupted = draft

    if error_type == "unexplained_jargon":
        # Inject dense mathematical & vector jargon without definition
        jargon_injection = (
            "\n\n### Mathematical Foundations of Retrieval\n"
            "To understand RAG deeply, we must compute the pairwise Cosine Similarity "
            "across 1536-dimensional dense vector embeddings in non-Euclidean latent Hilbert space. "
            "The top-K nearest neighbors are derived using Hierarchical Navigable Small World (HNSW) "
            "graphs under an anisotropic dot-product loss function before computing token logit distributions."
        )
        # Append into the middle of the document
        if "## How RAG Works" in corrupted:
            corrupted = corrupted.replace("## How RAG Works", "## How RAG Works" + jargon_injection)
        else:
            corrupted += jargon_injection

    elif error_type == "missing_why":
        # Remove the 'Why' section or replace it with a brief generic sentence
        # Look for headers containing 'Why'
        pattern = r"## (?:2\.\s*)?Why (?:Do We Need|is) RAG.*?(?=##|\Z)"
        match = re.search(pattern, corrupted, flags=re.DOTALL | re.IGNORECASE)
        if match:
            corrupted = corrupted[:match.start()] + corrupted[match.end():]
        else:
            # Fallback: remove paragraphs discussing why LLMs need RAG
            corrupted = re.sub(r"(?i)why we need.*?(\n\n##|\Z)", "\n\n", corrupted)

    elif error_type == "dense_vocabulary":
        # Replace simple phrases with convoluted, high-syllable academic prose
        replacements = {
            "easy": "epistemologically facile",
            "simple": "rudimentary and non-convoluted",
            "search": "execute exogenous heuristic query vectorization",
            "book": "codex repository",
            "student": "scholastic practitioner",
            "exam": "comprehensive summative academic evaluation",
            "answer": "synthesize an authoritative pedagogical exposition",
            "mistake": "anomalous hallucinations resulting from stochastic variance",
        }
        for simple_w, dense_w in replacements.items():
            corrupted = re.sub(rf"\b{simple_w}\b", dense_w, corrupted, flags=re.IGNORECASE)
        
        # Add an overly academic introductory disclaimer
        academic_header = (
            "> **Epistemological Disclaimer**: The pedagogical efficacy of this didactic exposition "
            "hinges upon the learner's intrinsic comprehension of computational linguistics and "
            "probabilistic matrix factorization paradigms.\n\n"
        )
        corrupted = academic_header + corrupted

    elif error_type == "factual_error":
        # Inject a false claim that RAG retrains the model weights
        false_claim = (
            "\n\n> **Important Core Fact**: When RAG finds a document, it immediately **retrains and updates "
            "the neural weights of the AI model permanently**. Every new document changes the internal "
            "brain weights of the LLM via backpropagation in real-time.\n\n"
        )
        if "## What is RAG" in corrupted:
            corrupted = corrupted.replace("## What is RAG", "## What is RAG" + false_claim)
        else:
            corrupted = false_claim + corrupted

    return corrupted
