"""Streamlit Interactive Visual Studio for Content Systems Agent."""

import json
import difflib
import streamlit as st
from pathlib import Path
import sys

# Ensure root dir is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from content_agent.graph import run_content_pipeline
from content_agent.memory import memory_store
from content_agent.error_injector import DELIBERATE_ERROR_TYPES
from content_agent.config import (
    RUBRIC_CHECKPOINTS,
    TARGET_PERSONA,
)

st.set_page_config(
    page_title="Content Systems | Self-Evaluating Lesson Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #757575;
        margin-bottom: 1.5rem;
    }
    .status-card {
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .pass-card {
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        color: #1B5E20;
    }
    .fail-card {
        background-color: #FFEBEE;
        border-left: 5px solid #F44336;
        color: #B71C1C;
    }
    .badge-pass {
        background-color: #4CAF50;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #F44336;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .diff-del {
        background-color: #ffeef0;
        color: #b31d28;
        text-decoration: line-through;
    }
    .diff-add {
        background-color: #e6ffed;
        color: #22863a;
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    st.sidebar.title("⚙️ Pipeline Controls")
    
    topic = st.sidebar.text_input(
        "Lesson Topic",
        value="Introduction to RAG (Retrieval-Augmented Generation)",
        help="Topic to generate and self-evaluate.",
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ LLM Engine Provider")
    model_mapping = {
        "Groq (openai/gpt-oss-120b - Ultra Powerful)": "openai/gpt-oss-120b",
        "Groq (openai/gpt-oss-20b - Fast)": "openai/gpt-oss-20b",
        "Groq (qwen/qwen3.6-27b)": "qwen/qwen3.6-27b",
    }
    provider_choice = st.sidebar.selectbox(
        "Active Model Provider",
        options=list(model_mapping.keys()),
        index=0,
        help="Select the LLM engine to use for generation and evaluation.",
    )
    import os
    os.environ["PRIMARY_MODEL"] = model_mapping[provider_choice]

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Target Learner Persona")
    with st.sidebar.expander("View Persona Calibration", expanded=False):
        st.info(TARGET_PERSONA)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧪 Fault Injection Testing")
    error_options = {"None (Normal Pass Flow)": None}
    for k, v in DELIBERATE_ERROR_TYPES.items():
        error_options[f"⚠️ {v['label']}"] = k

    selected_error_label = st.sidebar.selectbox(
        "Inject Deliberate Fault (Draft 1)",
        options=list(error_options.keys()),
        help="Select a fault to inject into Draft 1 to test if the Evaluator catches it and the Generator self-corrects.",
    )
    selected_error = error_options[selected_error_label]

    if selected_error:
        st.sidebar.warning(f"Active Fault: {DELIBERATE_ERROR_TYPES[selected_error]['description']}")

    max_retries = st.sidebar.slider("Max Retries", min_value=1, max_value=3, value=2, help="Maximum number of self-correction retry attempts.")

    return topic, selected_error, max_retries


def main():
    topic, deliberate_error, max_retries = render_sidebar()

    st.markdown('<div class="main-header">🎓 Self-Evaluating Lesson Content Generator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Autonomous Agentic Loop: <b>Generate</b> → <b>Strict Binary Rubric Evaluation</b> → <b>Diagnosis</b> → <b>Targeted Regeneration</b> → <b>Self-Evolving Memory</b></div>',
        unsafe_allow_html=True
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        start_btn = st.button("🚀 Run Agentic Pipeline", type="primary", use_container_width=True)

    if start_btn:
        with st.spinner("🤖 Executing LangGraph workflow (Generating, Evaluating & Auditing)..."):
            result = run_content_pipeline(
                topic=topic,
                deliberate_error=deliberate_error,
                max_retries=max_retries,
            )
            st.session_state["pipeline_result"] = result

    if "pipeline_result" in st.session_state:
        result = st.session_state["pipeline_result"]
        final_status = result.get("final_status", "UNKNOWN")
        draft_history = result.get("draft_history", [])
        rejection_log = result.get("rejection_log", [])
        eval_report = result.get("eval_report", {})
        current_draft = result.get("current_draft", "")

        # Status Banner
        if final_status == "PASSED":
            st.markdown(f"""
            <div class="status-card pass-card">
                <h3>🏆 Pipeline Status: PASSED (Quality Cleared for Shipping)</h3>
                <p>Total Drafts Generated: <b>{len(draft_history)}</b> | Rejections Diagnosed & Fixed: <b>{len(rejection_log)}</b></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-card fail-card">
                <h3>⚠️ Pipeline Status: FAILED (Max Retries Reached)</h3>
                <p>Total Drafts Generated: <b>{len(draft_history)}</b> | Rejections: <b>{len(rejection_log)}</b></p>
            </div>
            """, unsafe_allow_html=True)

        # Tabs Layout
        tab_lesson, tab_rubric, tab_diff, tab_rejections, tab_memory = st.tabs([
            "📄 Final Lesson",
            "📋 Rubric Scorecard",
            "🔄 Self-Correction Diff",
            "📊 Rejection Audit Log",
            "🧠 Long-Term Memory",
        ])

        with tab_lesson:
            st.subheader(f"Lesson: {topic}")
            st.download_button(
                label="📥 Download Lesson Markdown",
                data=current_draft,
                file_name="LESSON_INTRODUCTION_TO_RAG.md",
                mime="text/markdown",
            )
            st.markdown("---")
            st.markdown(current_draft)

        with tab_rubric:
            st.subheader("Strict Binary Rubric Evaluation (Zero Partial Credit)")
            if eval_report:
                checks = eval_report.get("checks", {})
                st.write(f"**Audit Summary:** {eval_report.get('summary', '')}")
                st.markdown("---")

                for key, check in checks.items():
                    passed = check.get("passed", False)
                    col_title, col_status = st.columns([4, 1])
                    with col_title:
                        st.markdown(f"#### {check.get('title', key)}")
                    with col_status:
                        if passed:
                            st.markdown('<span class="badge-pass">✓ PASS</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-fail">✗ FAIL</span>', unsafe_allow_html=True)

                    st.markdown(f"**Reasoning:** {check.get('reasoning', '')}")
                    if not passed and check.get("offending_snippet"):
                        st.warning(f"**Offending Snippet:** \"{check.get('offending_snippet')}\"")
                    if not passed and check.get("remediation_instruction"):
                        st.info(f"**Required Fix:** {check.get('remediation_instruction')}")
                    st.markdown("---")

        with tab_diff:
            st.subheader("Self-Correction & Revision Trace")
            if len(draft_history) > 1:
                st.info(f"Comparing **Draft 1 (Failed/Corrupted)** vs **Draft {len(draft_history)} (Revised & Passed)**")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("### ❌ Draft 1 (Initial / Rejected)")
                    st.text_area("Draft 1 Content", draft_history[0]["content"], height=500)
                with col_d2:
                    st.markdown("### ✅ Revised Draft (Self-Corrected)")
                    st.text_area("Final Draft Content", draft_history[-1]["content"], height=500)
            else:
                st.success("Draft 1 passed all 6 rubric checkpoints on the first attempt! No revision was required.")

        with tab_rejections:
            st.subheader("Structured Rejection Audit Trail")
            if rejection_log:
                st.json(rejection_log)
            else:
                st.write("No rejections occurred. The content cleared on initial generation.")

        with tab_memory:
            st.subheader("🧠 Persistent Self-Evolving Rules (Stored Across Runs)")
            rules_data = memory_store.export_evolved_rules_json()
            st.write(f"Total Active Learned Rules: **{rules_data.get('total_rules', 0)}**")
            
            for r in rules_data.get("evolved_rules", []):
                with st.expander(f"Rule: {r['rule_id']} (Observed {r['occurrences']}x)", expanded=True):
                    st.markdown(f"**Pattern:** {r['pattern']}")
                    st.markdown(f"**Learned Instruction:** {r['instruction']}")
                    st.caption(f"Last updated: {r['last_observed']}")


if __name__ == "__main__":
    main()
