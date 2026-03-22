"""Router node: classifies the query and selects a retrieval strategy.

Uses Claude Haiku via LangChain to detect the signal_type and choose between
SQL, vector, or keyword retrieval. Returns a state patch with router_output,
signal_type, and retrieval_strategy.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


def router_node(state: PipelineState) -> dict[str, Any]:
    """Classify the query and select a retrieval strategy.

    Calls Claude Haiku with a structured prompt to detect:
      - signal_type: classifier | report | enforcement | model_output
      - retrieval_strategy: sql | vector | keyword

    Strategies already in state["strategy_history"] are excluded from
    consideration so that retries pick an alternative approach.

    Args:
        state: Current pipeline state. Uses state["query"] and
            state["strategy_history"].

    Returns:
        State patch with keys: signal_type, retrieval_strategy, router_output.

    Raises:
        NotImplementedError: LLM call not yet implemented.
    """
    raise NotImplementedError("Router LLM call not yet implemented")
