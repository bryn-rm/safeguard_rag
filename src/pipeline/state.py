"""PipelineState: single source of truth for the LangGraph pipeline.

All nodes read from and write to this TypedDict. No data is passed between
nodes outside of the state object.
"""

from typing import Any

from typing_extensions import TypedDict


class PipelineState(TypedDict):
    """Shared state threaded through every node in the LangGraph pipeline.

    Attributes:
        query: The raw user query string.
        signal_type: Detected signal type (classifier, report, enforcement,
            model_output). Set by the router node.
        router_output: Full structured output from the router node, including
            rationale and confidence in the routing decision.
        retrieval_strategy: Active strategy chosen by the router:
            "sql" | "vector" | "keyword".
        retrieved_context: List of retrieved documents or SQL rows, each as
            a plain dict. Populated by whichever retrieval node runs.
        synthesised_answer: Natural-language answer produced by the
            synthesiser node.
        confidence_score: Float in [0, 1] assigned by the scorer node.
            None until scoring completes.
        failure_reason: Human-readable reason set when a node fails or when
            the scorer judges the answer insufficient.
        retry_count: Number of retries attempted so far. Incremented by the
            retry controller before re-entering the router.
        strategy_history: Ordered list of retrieval strategies that have
            already been tried, so the router can pick an alternative.
        metadata: Catch-all bag for observability tags (LangSmith run ID,
            wall-clock timings, model IDs, etc.).
    """

    query: str
    signal_type: str | None
    router_output: dict[str, Any] | None
    retrieval_strategy: str | None
    retrieved_context: list[dict[str, Any]]
    synthesised_answer: str | None
    confidence_score: float | None
    failure_reason: str | None
    retry_count: int
    strategy_history: list[str]
    metadata: dict[str, Any]


def initial_state(query: str) -> PipelineState:
    """Return a fresh PipelineState for the given query.

    Args:
        query: The user query to process.

    Returns:
        A PipelineState with all optional fields set to their zero values.
    """
    return PipelineState(
        query=query,
        signal_type=None,
        router_output=None,
        retrieval_strategy=None,
        retrieved_context=[],
        synthesised_answer=None,
        confidence_score=None,
        failure_reason=None,
        retry_count=0,
        strategy_history=[],
        metadata={},
    )
