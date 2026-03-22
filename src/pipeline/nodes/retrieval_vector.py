"""Vector retrieval node: nearest-neighbour search via pgvector.

Embeds the query with text-embedding-3-small, retrieves top-k neighbours
from pgvector with cosine similarity, applies MMR reranking, and returns
the results as retrieved_context.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


async def retrieval_vector_node(state: PipelineState) -> dict[str, Any]:
    """Embed the query and retrieve nearest neighbours from pgvector.

    Uses MMR reranking (applied in vector_store.py). Do not add a second
    reranking step downstream.

    Args:
        state: Current pipeline state. Uses state["query"].

    Returns:
        State patch with keys: retrieved_context, retrieval_strategy.

    Raises:
        NotImplementedError: Embedding and pgvector calls not yet implemented.
    """
    raise NotImplementedError("Vector retrieval not yet implemented")
