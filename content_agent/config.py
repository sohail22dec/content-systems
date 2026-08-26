"""Configuration, constants, prompts, and LLM factory for Content Systems."""

import os
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default Models
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "qwen/qwen3.6-27b")

# Storage Paths
STORAGE_DIR = ROOT_DIR / "storage"
OUTPUTS_DIR = ROOT_DIR / "outputs"
DOCS_DIR = ROOT_DIR / "docs"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STORAGE_DIR / "memory.db"
EVOLVED_RULES_PATH = OUTPUTS_DIR / "evolved_rules.json"
REJECTION_LOG_PATH = OUTPUTS_DIR / "rejection_log.json"
PASSED_LESSON_PATH = OUTPUTS_DIR / "LESSON_INTRODUCTION_TO_RAG.md"

# Target Persona Definition
TARGET_PERSONA = """
Target Learner Profile:
- Education: 12th-grade graduate from India.
- Background: Non-English-medium schooling (Hindi, Telugu, Tamil, Marathi, etc.), transitioning to English for tech.
- Vocabulary Level: Limited English vocabulary (A2 to early B1 CEFR level). Simple words, short sentences.
- Goal: Wants to understand foundational AI concepts to kickstart an AI career.
- Prior Knowledge: Absolute zero prerequisite knowledge in AI, machine learning, or complex mathematics.
- Learning Preference: Needs relatable daily-life analogies from everyday Indian context (e.g., open-book vs closed-book exams, student asking a school librarian, chef looking at recipe cards), step-by-step visual flows, concrete before abstract, zero unexplained jargon.
"""

# Rubric Dimensions (Strict Binary Checkpoints)
RUBRIC_CHECKPOINTS = {
    "grounded_accuracy": {
        "title": "Grounded Technical Accuracy",
        "description": "The lesson must explain the exact mechanism of RAG (Retrieval-Augmented Generation) correctly without any technical hallucinations or false claims.",
        "pass_criteria": "Accurately represents RAG as fetching external reference documents and providing them to an LLM context to ground the generation without retraining or fine-tuning the model weights.",
        "fail_criteria": "Claims RAG retrains/fine-tunes model weights, confuses RAG with prompt chaining, or provides incorrect factual information about how RAG works."
    },
    "vocabulary_accessibility": {
        "title": "Beginner-Friendly Language & Vocabulary",
        "description": "Language must be easily readable by a 12th-grade student with limited English vocabulary from a non-English-medium background.",
        "pass_criteria": "Uses simple, clear English, short sentences (under 15-20 words where possible), active voice, and plain conversational phrasing.",
        "fail_criteria": "Contains dense academic prose, convoluted multi-clause sentences, or obscure high-syllable words (e.g., 'epistemological', 'paradigm', 'ubiquitous', 'syntactical nuances') without simple synonyms."
    },
    "pedagogical_analogy": {
        "title": "Relatable Concrete Analogy",
        "description": "Must teach the core concept through a vivid, intuitive everyday analogy before diving into technical details.",
        "pass_criteria": "Includes a strong, intuitive everyday analogy (such as an Open-Book Exam vs. Closed-Book Exam, or a Chef with a Recipe Binder) that directly maps to the Retriever and Generator components.",
        "fail_criteria": "Lacks an everyday analogy or uses an abstract/confusing analogy that requires prior computer science knowledge."
    },
    "unexplained_jargon_guard": {
        "title": "Zero Unexplained Jargon Guard",
        "description": "Every technical term used must be immediately unpacked with simple words before or right when it appears.",
        "pass_criteria": "Every technical term (e.g., LLM, Hallucination, Retrieval, Context Window, Vector/Embedding) is instantly translated into plain English upon first mention.",
        "fail_criteria": "Drops technical jargon (e.g., 'Cosine Similarity', 'Vector Embeddings', 'Latent Space', 'Tokens', 'Loss Function', 'Hyperparameters') without immediate plain-English explanation."
    },
    "core_coverage": {
        "title": "Complete Core Coverage (What, Why, How)",
        "description": "Must cover the three fundamental pillars of the topic completely.",
        "pass_criteria": "Clearly and distinctly covers: (1) WHAT RAG is, (2) WHY it is needed (LLM knowledge cutoff date and making up facts/hallucinations), and (3) HOW it works step-by-step (Ask -> Search/Retrieve -> Combine/Augment -> Generate answer).",
        "fail_criteria": "Omits any of the three pillars (missing the 'Why', missing the 'How step-by-step', or failing to define 'What it is')."
    },
    "pedagogical_flow": {
        "title": "Coherent Pedagogical Flow & Practice",
        "description": "The lesson must flow logically from hook to conclusion and include an active comprehension check.",
        "pass_criteria": "Follows a clean progression: Engaging Hook -> Relatable Analogy -> The Core Problem -> The RAG Solution -> Step-by-Step Mechanism -> Real-World Example -> Quick Interactive Quiz (with answers).",
        "fail_criteria": "Disorganized jump between topics, missing a wrap-up or missing an active comprehension check (Quiz/Question)."
    }
}


def clean_llm_response(text: str) -> str:
    """Clean reasoning tokens or think tags from model outputs."""
    if not text:
        return ""
    # Strip <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def get_llm(provider: Optional[str] = None, temperature: float = 0.2) -> BaseChatModel:
    """Instantiate Chat Model with primary and fallback support."""
    # Primary: Gemini (free, fast, clean structured outputs)
    if (provider == "gemini" or (provider is None and GEMINI_API_KEY)) and GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=PRIMARY_MODEL if "gemini" in PRIMARY_MODEL else "gemini-2.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=temperature,
                max_output_tokens=4096,
            )
        except Exception:
            if not GROQ_API_KEY:
                raise

    # Fallback / Secondary: Groq Qwen
    if GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="qwen/qwen3.6-27b",
            groq_api_key=GROQ_API_KEY,
            temperature=temperature,
            max_tokens=4096,
        )

    raise ValueError("No valid API key found. Please provide GEMINI_API_KEY or GROQ_API_KEY in your .env file.")
