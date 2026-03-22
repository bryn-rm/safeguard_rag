"""Keyword retrieval node: BM25-style full-text search fallback.

Used when SQL and vector strategies have already been tried or are
inappropriate for the query. Searches the pgvector store using PostgreSQL
full-text search (tsvector / tsquery) rather than embedding similarity.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


async def retrieval_keyword_node(state: PipelineState) -> dict[str, Any]:
    """Run a full-text keyword search and return matching documents.

    Args:
        state: Current pipeline state. Uses state["query"].

    Returns:
        State patch with keys: retrieved_context, retrieval_strategy.

    Raises:
        NotImplementedError: Full-text search not yet implemented.
    """
    raise NotImplementedError("Keyword retrieval not yet implemented")
