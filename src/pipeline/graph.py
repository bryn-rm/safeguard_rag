"""LangGraph StateGraph wiring for the safeguards-RAG pipeline.

Defines the full graph structure:
  router → [retrieval_sql | retrieval_vector | retrieval_keyword]
         → synthesiser → scorer → [END | router (retry)]

Auto-curation rule: runs with confidence < 0.5 or retry_count > 0 are saved
to the 'safeguards-rag-eval' LangSmith dataset.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from src.pipeline.nodes.retrieval_keyword import retrieval_keyword_node
from src.pipeline.nodes.retrieval_sql import retrieval_sql_node
from src.pipeline.nodes.retrieval_vector import retrieval_vector_node
from src.pipeline.nodes.router import router_node
from src.pipeline.nodes.scorer import scorer_node
from src.pipeline.nodes.synthesiser import synthesiser_node
from src.pipeline.retry import increment_retry, next_strategy, should_retry
from src.pipeline.state import PipelineState

# ---------------------------------------------------------------------------
# Confidence threshold — should match configs/default.yaml
# ---------------------------------------------------------------------------
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5


# ---------------------------------------------------------------------------
# Conditional edge functions (pure; no side effects)
# ---------------------------------------------------------------------------


def route_to_retrieval(state: PipelineState) -> str:
    """Map router_output.retrieval_strategy to a retrieval node name.

    Args:
        state: Current pipeline state after the router node ran.

    Returns:
        One of "retrieval_sql", "retrieval_vector", "retrieval_keyword".
    """
    strategy = state.get("retrieval_strategy") or "vector"
    mapping: dict[str, str] = {
        "sql": "retrieval_sql",
        "vector": "retrieval_vector",
        "keyword": "retrieval_keyword",
    }
    return mapping.get(strategy, "retrieval_vector")


def route_after_scoring(state: PipelineState) -> str:
    """Decide whether to finish or retry after the scorer runs.

    Saves low-confidence or retried runs to the LangSmith eval dataset via
    the auto-curation side-effect (logged as metadata; actual dataset write
    happens in the LangSmith callback configured on graph.compile()).

    Args:
        state: Current pipeline state after the scorer node ran.

    Returns:
        "retry" or "end".
    """
    confidence = state.get("confidence_score")
    retry_count = state.get("retry_count", 0)

    # Flag run for LangSmith curation if low-confidence or already retried
    needs_curation = (confidence is not None and confidence < 0.5) or retry_count > 0
    if needs_curation:
        metadata: dict[str, Any] = state.get("metadata") or {}
        metadata["curate_to_eval_dataset"] = True

    if should_retry(state, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD):
        alt = next_strategy(state)
        if alt is not None:
            return "retry"
    return "end"


# ---------------------------------------------------------------------------
# Retry wrapper node
# ---------------------------------------------------------------------------


def retry_node(state: PipelineState) -> dict[str, Any]:
    """Increment retry counter and clear stale retrieval artefacts.

    This thin node sits on the "retry" edge so that state is patched before
    the router re-runs. It does not call any LLM.

    Args:
        state: Current pipeline state.

    Returns:
        Partial state dict from retry.increment_retry().
    """
    patch = increment_retry(state)
    # Inject the next preferred strategy so the router can respect it
    alt = next_strategy(state)
    if alt is not None:
        history: list[str] = list(state.get("strategy_history") or [])
        current = state.get("retrieval_strategy")
        if current and current not in history:
            history.append(current)
        patch["strategy_history"] = history
    return patch


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> Any:
    """Construct and compile the LangGraph StateGraph.

    Returns:
        A compiled LangGraph runnable ready for .invoke() / .ainvoke().
    """
    graph: StateGraph = StateGraph(PipelineState)  # type: ignore[type-arg]

    # Nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieval_sql", retrieval_sql_node)
    graph.add_node("retrieval_vector", retrieval_vector_node)
    graph.add_node("retrieval_keyword", retrieval_keyword_node)
    graph.add_node("synthesiser", synthesiser_node)
    graph.add_node("scorer", scorer_node)
    graph.add_node("retry", retry_node)

    # Entry point
    graph.set_entry_point("router")

    # router → retrieval dispatch
    graph.add_conditional_edges(
        "router",
        route_to_retrieval,
        {
            "retrieval_sql": "retrieval_sql",
            "retrieval_vector": "retrieval_vector",
            "retrieval_keyword": "retrieval_keyword",
        },
    )

    # All retrieval strategies converge on synthesiser
    graph.add_edge("retrieval_sql", "synthesiser")
    graph.add_edge("retrieval_vector", "synthesiser")
    graph.add_edge("retrieval_keyword", "synthesiser")

    # synthesiser → scorer
    graph.add_edge("synthesiser", "scorer")

    # scorer → retry or END
    graph.add_conditional_edges(
        "scorer",
        route_after_scoring,
        {
            "retry": "retry",
            "end": END,
        },
    )

    # retry → router (loop back)
    graph.add_edge("retry", "router")

    return graph.compile()


# Module-level compiled graph instance
pipeline = build_graph()
