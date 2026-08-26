"""LangGraph Orchestration Engine for Content Systems."""

from datetime import datetime
from typing import Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, START, END

from content_agent.state import AgentState, RubricEvaluation
from content_agent.generator import generate_lesson_draft
from content_agent.evaluator import evaluate_lesson
from content_agent.diagnostician import diagnose_rejection
from content_agent.error_injector import inject_deliberate_error
from content_agent.memory import memory_store
from content_agent.logger import print_evaluation_scorecard


def _parse_eval_report(eval_data: Any) -> Optional[RubricEvaluation]:
    """Safely parse or convert evaluation data into a RubricEvaluation instance."""
    if not eval_data:
        return None
    if isinstance(eval_data, RubricEvaluation):
        return eval_data
    if isinstance(eval_data, dict):
        try:
            return RubricEvaluation.model_validate(eval_data)
        except Exception:
            return None
    return None


def retrieve_memory_node(state: AgentState) -> Dict[str, Any]:
    """Node: Retrieve top evolved pedagogical rules from persistent long-term memory."""
    active_rules = memory_store.get_active_rules(limit=5)
    return {"learned_rules": active_rules}


def generator_node(state: AgentState) -> Dict[str, Any]:
    """Node: Generate initial lesson or surgically regenerate using diagnostic feedback."""
    topic = state.get("topic", "Introduction to RAG")
    learned_rules = state.get("learned_rules", [])
    revision_notes = state.get("revision_notes")
    previous_draft = state.get("current_draft")
    iteration = state.get("iteration", 0)

    draft = generate_lesson_draft(
        topic=topic,
        learned_rules=learned_rules,
        revision_notes=revision_notes,
        previous_draft=previous_draft if revision_notes else None,
    )

    draft_history = list(state.get("draft_history", []))
    draft_history.append({
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "content": draft,
        "is_revision": bool(revision_notes),
    })

    return {
        "current_draft": draft,
        "draft_history": draft_history,
        "revision_notes": None,  # Reset revision notes after consuming
    }


def error_injector_node(state: AgentState) -> Dict[str, Any]:
    """Node: Injects deliberate fault into first draft if error injection mode is active."""
    iteration = state.get("iteration", 0)
    deliberate_error = state.get("deliberate_error")
    current_draft = state.get("current_draft", "")

    # Only inject deliberate error on the very first draft (iteration 0)
    if deliberate_error and iteration == 0:
        corrupted_draft = inject_deliberate_error(current_draft, deliberate_error)
        draft_history = list(state.get("draft_history", []))
        if draft_history:
            draft_history[-1]["content"] = corrupted_draft
            draft_history[-1]["deliberate_error_applied"] = deliberate_error
        return {
            "current_draft": corrupted_draft,
            "draft_history": draft_history,
        }

    return {}


def evaluator_node(state: AgentState) -> Dict[str, Any]:
    """Node: Strictly evaluate draft against the 6-dimension binary rubric."""
    current_draft = state.get("current_draft", "")
    iteration = state.get("iteration", 0)

    eval_result = evaluate_lesson(current_draft)
    print_evaluation_scorecard(eval_result, iteration)

    return {
        "eval_report": eval_result.model_dump(),
    }


def diagnose_node(state: AgentState) -> Dict[str, Any]:
    """Node: Analyze failures and formulate surgical repair strategy for the next retry."""
    eval_report = _parse_eval_report(state.get("eval_report"))
    if not eval_report:
        current_draft = state.get("current_draft", "")
        eval_report = evaluate_lesson(current_draft)

    iteration = state.get("iteration", 0)
    rejection_record, revision_instructions = diagnose_rejection(eval_report, iteration)

    rejection_log = list(state.get("rejection_log", []))
    rejection_log.append(rejection_record.model_dump())

    return {
        "iteration": iteration + 1,
        "rejection_log": rejection_log,
        "revision_notes": revision_instructions,
    }


def memory_update_node(state: AgentState) -> Dict[str, Any]:
    """Node: Finalize workflow, record run in SQLite long-term store, and persist artifacts."""
    topic = state.get("topic", "Introduction to RAG")
    eval_report = _parse_eval_report(state.get("eval_report"))
    overall_pass = eval_report.overall_pass if eval_report else False
    final_status = "PASSED" if overall_pass else "FAILED"
    current_draft = state.get("current_draft", "")
    rejection_log = state.get("rejection_log", [])
    iteration = state.get("iteration", 0)
    eval_dict = eval_report.model_dump() if eval_report else {}

    # Save run trace to persistent long-term SQLite database
    run_id = memory_store.record_run(
        topic=topic,
        status=final_status,
        total_iterations=iteration + 1,
        final_draft=current_draft,
        eval_report=eval_dict,
        rejection_logs=rejection_log,
    )

    return {
        "final_status": final_status,
    }


def route_evaluation(state: AgentState) -> Literal["memory_update_node", "diagnose_node"]:
    """Conditional Edge: Route to memory_update_node on PASS or max retries, else diagnose_node."""
    eval_report = _parse_eval_report(state.get("eval_report"))
    iteration = state.get("iteration", 0)
    max_retries = state.get("max_retries", 2)

    if eval_report and eval_report.overall_pass:
        return "memory_update_node"

    if iteration >= max_retries:
        return "memory_update_node"

    return "diagnose_node"


def build_content_agent_graph() -> StateGraph:
    """Compile and return the LangGraph workflow."""
    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("retrieve_memory_node", retrieve_memory_node)
    builder.add_node("generator_node", generator_node)
    builder.add_node("error_injector_node", error_injector_node)
    builder.add_node("evaluator_node", evaluator_node)
    builder.add_node("diagnose_node", diagnose_node)
    builder.add_node("memory_update_node", memory_update_node)

    # Add Edges
    builder.add_edge(START, "retrieve_memory_node")
    builder.add_edge("retrieve_memory_node", "generator_node")
    builder.add_edge("generator_node", "error_injector_node")
    builder.add_edge("error_injector_node", "evaluator_node")

    # Conditional Routing from Evaluator
    builder.add_conditional_edges(
        "evaluator_node",
        route_evaluation,
        {
            "memory_update_node": "memory_update_node",
            "diagnose_node": "diagnose_node",
        }
    )

    # Loop back from Diagnostician to Generator
    builder.add_edge("diagnose_node", "generator_node")
    builder.add_edge("memory_update_node", END)

    return builder.compile()


def run_content_pipeline(
    topic: str = "Introduction to RAG",
    deliberate_error: Optional[str] = None,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """Execute the full agentic loop synchronously.

    Args:
        topic: The topic title to generate.
        deliberate_error: Optional deliberate fault to inject into draft 1.
        max_retries: Maximum number of regeneration attempts (default 2).

    Returns:
        Final state dictionary containing results, drafts, and rejection history.
    """
    app = build_content_agent_graph()
    initial_state: AgentState = {
        "topic": topic,
        "target_persona": "12th-grade graduate from India, limited English vocabulary",
        "iteration": 0,
        "max_retries": max_retries,
        "current_draft": "",
        "draft_history": [],
        "eval_report": None,
        "rejection_log": [],
        "deliberate_error": deliberate_error,
        "learned_rules": [],
        "revision_notes": None,
        "final_status": "IN_PROGRESS",
        "error_message": None,
    }

    final_state = app.invoke(initial_state)
    return final_state
