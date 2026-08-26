"""State definitions and Pydantic schemas for Content Systems agentic workflow."""

from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class RubricCheck(BaseModel):
    """Single checkpoint evaluation result."""
    name: str = Field(description="Internal identifier of the rubric checkpoint")
    title: str = Field(description="Human readable title of the checkpoint")
    passed: bool = Field(description="Strict boolean PASS (True) or FAIL (False)")
    reasoning: str = Field(description="Detailed explanation of why it passed or failed")
    offending_snippet: Optional[str] = Field(
        default=None,
        description="Exact quote or phrase from the lesson that triggered the failure, if failed"
    )
    remediation_instruction: Optional[str] = Field(
        default=None,
        description="Actionable instruction for the generator on how to fix this specific failure"
    )


class RubricEvaluation(BaseModel):
    """Aggregated evaluation across all binary checkpoints."""
    overall_pass: bool = Field(
        description="True ONLY if ALL individual checkpoints passed (zero partial credit)"
    )
    passed_count: int = Field(description="Number of passed checkpoints")
    total_count: int = Field(description="Total number of checkpoints evaluated")
    checks: Dict[str, RubricCheck] = Field(description="Dictionary mapping checkpoint name to RubricCheck")
    summary: str = Field(description="High level diagnostic summary of the evaluation")
    recommendation: str = Field(description="Recommended action (SHIP or REVISE)")


class RejectionRecord(BaseModel):
    """Audit log entry capturing a rejection event and the corrective plan."""
    iteration: int = Field(description="Iteration index at which the rejection occurred")
    timestamp: str = Field(description="ISO timestamp of rejection")
    failed_checkpoints: List[str] = Field(description="List of checkpoint names that failed")
    diagnostics: List[Dict[str, Any]] = Field(description="Detailed failure snippet and rationale per checkpoint")
    strategy_applied: str = Field(description="Specific prompt strategy and constraints injected for retry")


class EvolvedRule(BaseModel):
    """Learned guideline extracted from persistent failure patterns across runs."""
    rule_id: str = Field(description="Unique identifier for the evolved rule")
    pattern: str = Field(description="The recurring failure pattern detected")
    rule_instruction: str = Field(description="The actionable prompt constraint to prevent this failure")
    occurrences: int = Field(default=1, description="Number of times this pattern was observed")
    created_at: str = Field(description="Timestamp when rule was first extracted")


class AgentState(TypedDict):
    """State schema passed across LangGraph nodes."""
    topic: str
    target_persona: str
    iteration: int
    max_retries: int
    current_draft: str
    draft_history: List[Dict[str, Any]]
    eval_report: Optional[Dict[str, Any]]
    rejection_log: List[Dict[str, Any]]
    deliberate_error: Optional[str]
    learned_rules: List[str]
    revision_notes: Optional[str]
    final_status: str  # "IN_PROGRESS", "PASSED", "FAILED"
    error_message: Optional[str]
