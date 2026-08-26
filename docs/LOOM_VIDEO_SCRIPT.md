# 🎬 Loom Video Demonstration Script (15–20 Minutes)
**Role**: GenAI Engineer - Content Systems  
**Topic**: Self-Evaluating Lesson Content Generator ("Introduction to RAG")  
**Target Learner**: 12th-grade Indian graduate, non-English-medium background, limited English vocabulary  

---

## 🕒 Video Structure & Timestamp Guide

| Time | Section | Screen / Visual Focus | Key Discussion Points |
| :--- | :--- | :--- | :--- |
| **00:00 – 02:30** | **1. Introduction & Persona Alignment** | Webcam (Face visible) + Title Slide | Introduce self, role context, target persona calibration, and the core problem of static prompting vs autonomous agentic loops. |
| **02:30 – 06:00** | **2. Architecture & System Walkthrough** | Codebase / Mermaid Diagram in README | LangGraph StateGraph, Pedagogical Generator, Strict Binary Evaluator (Zero Partial Credit), Diagnostician, and Self-Evolving Long-Term Memory. |
| **06:00 – 10:30** | **3. End-to-End Live Workflow Demo** | Streamlit Web Studio (`ui/app.py`) | Run a clean generation pass on "Introduction to RAG". Walk through the 6-checkpoint binary rubric scorecard, pedagogical analogies, and quiz. |
| **10:30 – 15:30** | **4. Deliberate Error Catching & Self-Correction** | Streamlit UI + Terminal CLI | Inject a deliberate fault (`Unexplained Math Jargon` or `Dense Vocabulary`). Show Evaluator catching it (FAIL), generating Rejection Audit Log, Diagnostician formulating surgical fixes, and Generator producing a PASSED Draft 2. |
| **15:30 – 18:00** | **5. Persistent Memory & Self-Evolution** | SQLite / JSON Memory Inspector | Show cross-run pattern extraction: how persistent failure traces synthesize new prompt rules to prevent future regressions. |
| **18:00 – 20:00** | **6. Trade-offs & Production Next Steps** | Webcam + Architecture Summary | Model latency vs evaluation rigor, LLM-as-a-judge reliability guards, multi-modal diagrams, and closing. |

---

## 🎙️ Detailed Speaking Script (Word-for-Word Walkthrough)

### Section 1: Introduction & Persona Alignment (00:00 – 02:30)
**[Visual: Webcam full screen or PIP in top corner. Face clearly visible.]**

> *"Hello everyone! My name is [Your Name], and today I am thrilled to present my solution for the **GenAI Engineer - Content Systems** take-home assessment.*
>
> *In production content systems, creating educational material is never about writing a single clever prompt. If you rely on a single prompt, you have no guarantee of pedagogical clarity, no factual guardrails, and no self-healing mechanism when the model slips.*
>
> *Instead, what we need is an **autonomous agentic system** that generates content, audits its own quality against a strict binary rubric, diagnoses rejections, and iteratively refines the draft until it is truly good enough to ship to a student.*
>
> *Our target student profile is very specific: A **12th-grade graduate from India with a non-English-medium background and limited English vocabulary**, wanting to kickstart an AI career from zero.*
>
> *For this learner, dense academic words, complex math formulas, or unexplained jargon like 'cosine similarity in latent Hilbert space' will immediately cause frustration and drop-off. They need intuitive everyday analogies — like open-book versus closed-book exams — short sentences, and concrete examples before theory."*

---

### Section 2: Architecture & Workflow Design (02:30 – 06:00)
**[Visual: Screen share `README.md` showing the Mermaid Architecture diagram and `content_agent/graph.py`.]**

> *"Let’s look at the system architecture. I designed this workflow using **LangGraph**, giving us deterministic state transitions and cycle control.*
>
> *The pipeline consists of 5 core nodes:*
> 1. ***Persistent Memory Retriever***: *Fetches evolved pedagogical constraints learned from past runs.*
> 2. ***Pedagogical Generator***: *Drafts the lesson using simple vocabulary, relatable Indian metaphors, and memory-injected guidelines.*
> 3. ***Strict Binary Evaluator (Zero Partial Credit)***: *Audits the draft across 6 hard pass/fail checkpoints: Grounded Accuracy, Vocabulary Accessibility, Concrete Analogy, Zero Unexplained Jargon, Core Coverage (What, Why, How), and Pedagogical Flow.*
> 4. ***Diagnostician & Feedback Node***: *If ANY checkpoint fails, it captures the exact offending snippet, formulates a surgical remediation instruction, and logs a structured Rejection Record.*
> 5. ***Self-Evolving Memory Engine***: *Persists failure patterns to SQLite, tracks failure frequency across runs, and dynamically synthesizes new prompt rules.*
>
> *Notice that we enforce a strict termination limit of 1 to 2 retries, ensuring the loop never gets stuck in an infinite cycle."*

---

### Section 3: Live End-to-End Run (06:00 – 10:30)
**[Visual: Open Streamlit Web App (`streamlit run ui/app.py`).]**

> *"Let’s see the system in action. Here is our Interactive Visual Studio.*
>
> *I’ll select the topic **'Introduction to RAG'** with normal mode (no deliberate errors). Let's click **Run Agentic Pipeline**.*
>
> *[Point to screen as the spinner runs.]*
>
> *The graph has executed! Let’s inspect the output:*
> - *Under **Final Lesson**, notice how the lesson opens with a relatable analogy: the **Open-Book Exam vs. Closed-Book Exam**. It explains that a regular LLM takes a closed-book exam relying only on memory, while RAG gives the AI an open notebook.*
> - *It clearly answers the 3 pillars: What is RAG, Why it's needed (LLM knowledge cutoff & hallucination problem), and How it works in 4 simple steps.*
> - *It explicitly confirms that model weights are **never retrained or changed**.*
> - *It ends with a friendly 3-question Multiple Choice Quiz.*
>
> *Now let's switch to the **Rubric Scorecard** tab. Here, all 6 checkpoints show a bright green **✓ PASS** badge. Because all 6 passed, the overall recommendation is **SHIP**."*

---

### Section 4: Deliberate Error Catching & Self-Correction (10:30 – 15:30)
**[Visual: Streamlit sidebar dropdown -> Select '⚠️ Unexplained Math & Vector Jargon' or run `python -m ui.cli --inject-error unexplained_jargon`.]**

> *"Now, for the critical requirement of this assessment: **proving that our evaluator catches deliberate errors and that the generator self-corrects**.*
>
> *In the sidebar, I am enabling our test harness to inject **Unexplained Math Jargon** into Draft 1. This simulates a real-world edge case where the LLM accidentally dumps dense academic terms like 'Cosine Similarity across 1536-dimensional latent Hilbert space' into a beginner lesson.*
>
> *Let’s run the pipeline.*
>
> *[Wait for execution to complete.]*
>
> *Look at the result!*
> - *In **Draft 1**, the Evaluator immediately flagged the draft as **REJECTED (FAIL)**. Checkpoint 4 (`unexplained_jargon_guard`) failed!*
> - *The Evaluator extracted the exact quote: `'pairwise Cosine Similarity across 1536-dimensional dense vector embeddings'`.*
> - *The Diagnostician generated a structured Rejection Record and formulated a surgical prompt: 'Remove or explain Cosine Similarity in plain words; preserve the rest of the lesson structure.'*
> - *Then, the **Regenerator** executed Retry 1, surgically replacing the dense math with friendly note-matching explanations.*
> - *On the second evaluation pass, the Evaluator reviewed the revised draft, confirmed the jargon was removed, and issued a **✓ PASS (SHIP)**!*
>
> *Under the **Self-Correction Diff** tab, you can clearly see the side-by-side comparison: Draft 1 had the offending math block, and Draft 2 cleanly replaced it."*

---

### Section 5: Persistent Long-Term Memory & Self-Evolution (15:30 – 18:00)
**[Visual: Navigate to 'Long-Term Memory' tab or run `python -m ui.cli --list-rules`.]**

> *"Let’s look at how the system evolves across runs.*
>
> *Every time a rejection occurs, the failure signature is written to our SQLite database. The memory engine tracks how often specific failure patterns repeat across different topics.*
>
> *Here in the **Long-Term Memory** inspector, you can see our evolved rules. When the jargon failure occurred, the occurrence counter incremented, and the rule was prioritized in the generator's active prompt memory.*
>
> *This ensures that across hundreds of lesson generation runs, the system gets progressively smarter and avoids repeating past mistakes."*

---

### Section 6: Architectural Trade-offs & Production Next Steps (18:00 – 20:00)
**[Visual: Webcam full screen / closing slide.]**

> *"To wrap up, let's discuss the engineering trade-offs made in this design:*
> 1. ***Binary vs. Continuous Scoring***: *We chose a strict binary pass/fail rubric over a 1-to-10 scale. Continuous scales introduce evaluation drift and threshold ambiguity, whereas binary checkpoints provide zero-tolerance quality gates.*
> 2. ***Deterministic Guardrails on Top of LLM-as-a-Judge***: *Pure LLM evaluators can occasionally be too lenient. We layered regex and keyword guardrails into the evaluator to guarantee 100% catch rate on critical failures like false weight-retraining claims.*
> 3. ***Differential Regeneration vs. Full Rewrite***: *Instead of throwing away the entire draft, our Diagnostician instructs the Generator to preserve passing sections and repair only failing components, drastically saving token costs and preserving pedagogical coherence.*
>
> *In a full enterprise deployment, next steps would include adding multi-modal diagram generation (generating visual SVG flowcharts for visual learners) and integrating automated human-in-the-loop escalation.*
>
> *Thank you very much for your time and consideration!"*
