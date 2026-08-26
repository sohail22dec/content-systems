"""Pedagogical Generator & Differential Regenerator Node for Content Systems."""

from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from content_agent.config import TARGET_PERSONA, get_llm, clean_llm_response


GENERATOR_SYSTEM_PROMPT = """You are a Master AI Educator specializing in creating beginner-friendly learning content for young students in India.

TARGET STUDENT PERSONA:
{target_persona}

PEDAGOGICAL DESIGN PRINCIPLES:
1. Simplicity First: Use simple, conversational English words. Keep sentences short (under 15–20 words).
2. Grounded Analogies: Teach abstract ideas using familiar Indian daily-life metaphors (e.g., an Open-Book Exam vs. a Closed-Book Exam, a Student asking a Librarian, or a Chef with a Recipe Card).
3. Clear Core Pillars: You MUST thoroughly cover:
   - What is RAG? (Retrieval-Augmented Generation)
   - Why do we need it? (Explain LLM knowledge cutoffs and the hallucination problem where AI makes up facts).
   - How does it work step-by-step? (1. User asks question -> 2. Ingest/Store & Search/Retrieve -> 3. Augment/Combine -> 4. Generate answer).
4. Zero Unexplained Jargon: If you introduce any technical AI term (like LLM, Hallucination, Retrieval, Prompt), you MUST explain it immediately in plain, friendly words. NEVER use advanced math jargon (like Cosine Similarity, Latent Hilbert Space, or Dot Products).
5. Explicit Note on Weights: Mention clearly that RAG does NOT retrain or change the AI model's internal weights; it just provides notes to read.
6. Structured Flow: Organize with clear Markdown headers, bullet points, and visual text callouts.
7. Interactive Comprehension: Always end with a fun 3-question Multiple Choice Quiz with answers and friendly explanations.

{evolved_rules_section}
"""


def _build_evolved_rules_text(learned_rules: List[str]) -> str:
    if not learned_rules:
        return ""
    rules_list = "\n".join([f"- {r}" for r in learned_rules])
    return f"\n### 🧠 MEMORY-LEARNED GUIDELINES (Must strictly follow):\n{rules_list}\n"


def generate_lesson_draft(
    topic: str,
    learned_rules: Optional[List[str]] = None,
    revision_notes: Optional[str] = None,
    previous_draft: Optional[str] = None,
) -> str:
    """Generate a complete standalone beginner lesson or regenerate based on failure diagnosis."""
    llm = get_llm(temperature=0.3)
    rules_text = _build_evolved_rules_text(learned_rules or [])
    system_prompt = GENERATOR_SYSTEM_PROMPT.format(
        target_persona=TARGET_PERSONA,
        evolved_rules_section=rules_text
    )

    if revision_notes and previous_draft:
        # Differential Regeneration Mode
        user_prompt = (
            f"Topic: **{topic}**\n\n"
            f"{revision_notes}\n\n"
            f"--- PREVIOUS DRAFT (NEEDS REVISION) ---\n"
            f"{previous_draft}\n"
            f"--- END OF PREVIOUS DRAFT ---\n\n"
            f"Please generate the complete, revised, and polished standalone lesson in Markdown. "
            f"Ensure all feedback is addressed and all 6 rubric checkpoints will pass."
        )
    else:
        # Initial Generation Mode
        user_prompt = (
            f"Please write a complete, standalone beginner lesson teaching the topic: **'{topic}'**.\n\n"
            f"Remember:\n"
            f"- Target student: 12th-grade graduate from India with limited English vocabulary.\n"
            f"- Start with a relatable everyday analogy (like Open-Book vs Closed-Book Exam).\n"
            f"- Clearly explain: (1) What is RAG, (2) Why do we need it (hallucination & outdated knowledge), and (3) How it works step-by-step.\n"
            f"- Avoid all unexplained jargon.\n"
            f"- Include a 3-question practice quiz at the end with answers.\n"
            f"- Output complete formatted Markdown."
        )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return clean_llm_response(response.content)
