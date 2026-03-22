"""Retry controller for the LangGraph pipeline.

Controls whether the pipeline should retry with an alternative retrieval
strategy after a low-confidence answer. Max 2 retries; strategy exclusion
list lives in PipelineState.strategy_history.
"""

from __future__ import annotations

from src.pipeline.state import PipelineState

MAX_RETRIES: int = 2

# Ordered preference list: if a strategy is exhausted, try the next one.
STRATEGY_PREFERENCE: list[str] = ["sql", "vector", "keyword"]


def should_retry(state: PipelineState, confidence_threshold: float = 0.5) -> bool:
    """Return True if the pipeline should retry with an alternative strategy.

    Args:
        state: Current pipeline state after scoring.
        confidence_threshold: Minimum acceptable confidence score.

    Returns:
        True when retry is warranted (low confidence and retries remaining).
    """
    if state["retry_count"] >= MAX_RETRIES:
        return False
    score = state["confidence_score"]
    if score is None:
        return True
    return score < confidence_threshold


def next_strategy(state: PipelineState) -> str | None:
    """Select the next retrieval strategy, excluding already-tried ones.

    Args:
        state: Current pipeline state.

    Returns:
        The next strategy name, or None if all strategies are exhausted.
    """
    tried = set(state["strategy_history"])
    for strategy in STRATEGY_PREFERENCE:
        if strategy not in tried:
            return strategy
    return None


def increment_retry(state: PipelineState) -> dict[str, object]:
    """Return a state patch that increments retry_count and clears stale fields.

    This is called by the retry edge handler before re-entering the router.

    Args:
        state: Current pipeline state.

    Returns:
        Partial state dict to merge into the graph state.
    """
    return {
        "retry_count": state["retry_count"] + 1,
        "retrieved_context": [],
        "synthesised_answer": None,
        "confidence_score": None,
        "failure_reason": None,
    }
