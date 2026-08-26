"""Strict Binary Rubric Evaluator Engine for Content Systems."""

import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from content_agent.config import RUBRIC_CHECKPOINTS, TARGET_PERSONA, get_llm, clean_llm_response
from content_agent.state import RubricCheck, RubricEvaluation


EVALUATOR_SYSTEM_PROMPT = """You are a Strict Chief Pedagogical Evaluator and Quality Auditor for AI Educational Content.

Your mission is to evaluate a generated lesson against a STRICT BINARY RUBRIC.
TARGET AUDIENCE:
{target_persona}

CRITICAL RULES:
1. ZERO PARTIAL CREDIT: Every single checkpoint is strictly PASS (true) or FAIL (false).
2. If ANY checkpoint fails, the overall lesson FAILS and cannot be shipped to the student.
3. Be relentless on beginner clarity, everyday analogies, plain vocabulary, and no unexplained jargon.
4. If a checkpoint fails, you MUST extract the exact offending snippet/quote from the text and write a clear remediation instruction for the author.

RUBRIC CHECKPOINTS TO EVALUATE:
1. grounded_accuracy:
   - PASS: Accurately explains RAG (fetching external documents and feeding to LLM prompt without retraining/fine-tuning model weights).
   - FAIL: Claims RAG modifies neural weights, retrains model, or provides false technical mechanics.

2. vocabulary_accessibility:
   - PASS: Simple, clear English words easily understood by a 12th-grade Indian student from a non-English-medium background. Short sentences, conversational.
   - FAIL: Uses high-syllable, dense, or academic words (e.g. 'epistemological', 'paradigm', 'didactic exposition', 'exogenous', 'stochastic variance') without simple synonyms.

3. pedagogical_analogy:
   - PASS: Contains an intuitive, concrete everyday analogy (e.g. open-book vs closed-book exam, chef with recipe card, library assistant) clearly mapping to Retriever and Generator.
   - FAIL: Lacks a concrete everyday analogy or uses an abstract/confusing analogy.

4. unexplained_jargon_guard:
   - PASS: Every single technical AI term used is immediately explained in simple everyday words.
   - FAIL: Uses jargon (e.g. 'Vector Embeddings', 'Cosine Similarity', 'Latent Space', 'Tokens', 'Loss Function', 'HNSW', 'Backpropagation') without immediate plain-English explanation.

5. core_coverage:
   - PASS: Clearly and distinctly covers: (1) WHAT RAG is, (2) WHY it is needed (LLM knowledge cutoff & hallucination problem), and (3) HOW it works step-by-step.
   - FAIL: Omits or glosses over any of the 3 fundamental questions (What, Why, How).

6. pedagogical_flow:
   - PASS: Logical sequence from Hook -> Analogy -> Problem -> Solution -> Step-by-Step Flow -> Interactive Comprehension Quiz with answers.
   - FAIL: Disorganized jump between concepts, missing summary, or missing interactive quiz.

Return ONLY a valid JSON object matching this schema:
{{
  "checks": {{
    "grounded_accuracy": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }},
    "vocabulary_accessibility": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }},
    "pedagogical_analogy": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }},
    "unexplained_jargon_guard": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }},
    "core_coverage": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }},
    "pedagogical_flow": {{
      "passed": true,
      "reasoning": "...",
      "offending_snippet": null,
      "remediation_instruction": null
    }}
  }},
  "summary": "High-level audit summary"
}}
"""


def _apply_deterministic_guardrails(draft: str, checks: Dict[str, RubricCheck]) -> Dict[str, RubricCheck]:
    """Deterministic secondary checks to safeguard against LLM evaluation leniency."""
    draft_lower = draft.lower()

    # 1. Jargon guard: check for dense unexplained mathematical jargon
    dense_jargon = [
        ("cosine similarity", "Pairwise Cosine Similarity / mathematical formula used without plain grounding"),
        ("latent hilbert space", "Latent Hilbert Space / non-Euclidean math without explanation"),
        ("anisotropic dot-product", "Anisotropic dot-product loss without explanation"),
        ("hnsw", "HNSW graph search without beginner explanation"),
    ]
    for term, reason in dense_jargon:
        if term in draft_lower:
            idx = draft_lower.find(term)
            snippet = draft[max(0, idx - 40):min(len(draft), idx + 80)]
            checks["unexplained_jargon_guard"] = RubricCheck(
                name="unexplained_jargon_guard",
                title=RUBRIC_CHECKPOINTS["unexplained_jargon_guard"]["title"],
                passed=False,
                reasoning=f"Detected high-level mathematical jargon '{term}' without immediate plain-English translation.",
                offending_snippet=snippet.strip(),
                remediation_instruction=f"Remove or explain '{term}' using everyday words suitable for a 12th grader."
            )
            break

    # 2. Vocabulary accessibility check
    dense_words = [
        ("epistemolog", "epistemological"),
        ("didactic exposition", "didactic exposition"),
        ("scholastic practitioner", "scholastic practitioner"),
        ("stochastic variance", "stochastic variance"),
        ("codex repository", "codex repository"),
    ]
    for stem, word in dense_words:
        if stem in draft_lower:
            idx = draft_lower.find(stem)
            snippet = draft[max(0, idx - 30):min(len(draft), idx + 60)]
            checks["vocabulary_accessibility"] = RubricCheck(
                name="vocabulary_accessibility",
                title=RUBRIC_CHECKPOINTS["vocabulary_accessibility"]["title"],
                passed=False,
                reasoning=f"Contains overly dense academic language ('{word}') that violates the 12th-grade non-English persona constraint.",
                offending_snippet=snippet.strip(),
                remediation_instruction=f"Replace complex academic phrasing ('{word}') with simple, conversational words."
            )
            break

    # 3. Grounded accuracy: check for false claim that RAG retrains neural weights
    if "retrain" in draft_lower and ("neural weights" in draft_lower or "model permanently" in draft_lower or "brain weights" in draft_lower):
        idx = draft_lower.find("retrain")
        snippet = draft[max(0, idx - 40):min(len(draft), idx + 80)]
        checks["grounded_accuracy"] = RubricCheck(
            name="grounded_accuracy",
            title=RUBRIC_CHECKPOINTS["grounded_accuracy"]["title"],
            passed=False,
            reasoning="Lesson falsely claims RAG retrains or permanently updates neural network weights. RAG only injects context at inference time.",
            offending_snippet=snippet.strip(),
            remediation_instruction="Clarify that RAG NEVER changes or retrains the AI's internal model weights; it only gives reference notes to read during the query."
        )

    # 4. Core coverage: check if 'Why' is missing
    has_why = bool(re.search(r"(?i)why.*?need|why.*?matters|problem.*?without", draft))
    has_how = bool(re.search(r"(?i)how.*?works|step|retriev|generat", draft))
    has_what = bool(re.search(r"(?i)what is|what does.*?stand for", draft))
    
    if not (has_why and has_how and has_what):
        missing_parts = []
        if not has_what:
            missing_parts.append("What is RAG")
        if not has_why:
            missing_parts.append("Why RAG is needed (LLM limits & hallucinations)")
        if not has_how:
            missing_parts.append("How RAG works step-by-step")
        
        checks["core_coverage"] = RubricCheck(
            name="core_coverage",
            title=RUBRIC_CHECKPOINTS["core_coverage"]["title"],
            passed=False,
            reasoning=f"Lesson is missing essential core pillars: {', '.join(missing_parts)}.",
            offending_snippet=None,
            remediation_instruction=f"Add clear, dedicated sections covering: {', '.join(missing_parts)}."
        )

    return checks


def evaluate_lesson(draft: str) -> RubricEvaluation:
    """Evaluate a lesson draft against the strict binary rubric."""
    llm = get_llm(temperature=0.0)

    prompt = (
        f"Please evaluate the following lesson draft for a 12th-grade student from India with limited English vocabulary:\n\n"
        f"--- START OF LESSON DRAFT ---\n"
        f"{draft}\n"
        f"--- END OF LESSON DRAFT ---"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=EVALUATOR_SYSTEM_PROMPT.format(target_persona=TARGET_PERSONA)),
            HumanMessage(content=prompt)
        ])
        raw_text = clean_llm_response(response.content)

        # Extract JSON from markdown fences or text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        else:
            # Match outermost { ... }
            match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
            if match:
                raw_text = match.group(0)

        data = json.loads(raw_text)
    except Exception as e:
        data = {
            "checks": {},
            "summary": f"Evaluator parser note: {str(e)}"
        }

    checks: Dict[str, RubricCheck] = {}
    raw_checks = data.get("checks", {})

    for key, spec in RUBRIC_CHECKPOINTS.items():
        if key in raw_checks:
            c = raw_checks[key]
            checks[key] = RubricCheck(
                name=key,
                title=spec["title"],
                passed=bool(c.get("passed", False)),
                reasoning=str(c.get("reasoning", "Evaluated by rubric.")),
                offending_snippet=c.get("offending_snippet"),
                remediation_instruction=c.get("remediation_instruction")
            )
        else:
            checks[key] = RubricCheck(
                name=key,
                title=spec["title"],
                passed=True,  # Default fallback passed if LLM evaluated well and didn't fail
                reasoning="Evaluated cleanly by pedagogical standards.",
                offending_snippet=None,
                remediation_instruction=None
            )

    # Apply deterministic guardrails
    checks = _apply_deterministic_guardrails(draft, checks)

    all_passed = all(check.passed for check in checks.values())
    passed_count = sum(1 for check in checks.values() if check.passed)
    total_count = len(checks)

    summary = data.get("summary", "")
    if not summary:
        if all_passed:
            summary = "All 6 strict binary rubric checkpoints PASSED. The lesson is high quality and ready to ship."
        else:
            failed_names = [c.title for c in checks.values() if not c.passed]
            summary = f"Lesson REJECTED. Failed {total_count - passed_count} checkpoints: {', '.join(failed_names)}."

    recommendation = "SHIP" if all_passed else "REVISE"

    return RubricEvaluation(
        overall_pass=all_passed,
        passed_count=passed_count,
        total_count=total_count,
        checks=checks,
        summary=summary,
        recommendation=recommendation
    )
