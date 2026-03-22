"""pgvector client for similarity search and MMR reranking.

Connects to PostgreSQL with the pgvector extension. Cosine similarity is used
by default. MMR reranking is applied here — do not add a second reranking step
downstream.
"""

from __future__ import annotations

from typing import Any


async def similarity_search(
    query_embedding: list[float],
    top_k: int = 10,
    filter_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve top-k nearest neighbours by cosine similarity.

    Args:
        query_embedding: Dense query vector.
        top_k: Number of candidates to retrieve before reranking.
        filter_metadata: Optional metadata filter applied before search.

    Returns:
        List of document dicts with keys: id, content, metadata, score.

    Raises:
        NotImplementedError: pgvector connection not yet implemented.
    """
    raise NotImplementedError("pgvector similarity search not yet implemented")


def mmr_rerank(
    query_embedding: list[float],
    candidates: list[dict[str, Any]],
    top_k: int = 5,
    lambda_mult: float = 0.5,
) -> list[dict[str, Any]]:
    """Apply Maximal Marginal Relevance reranking to reduce redundancy.

    MMR balances relevance to the query against diversity among selected
    documents. lambda_mult=1.0 is pure relevance; 0.0 is pure diversity.

    Args:
        query_embedding: Dense query vector.
        candidates: Candidate documents from similarity_search.
        top_k: Number of documents to return after reranking.
        lambda_mult: Trade-off between relevance and diversity.

    Returns:
        Reranked list of up to top_k document dicts.

    Raises:
        NotImplementedError: MMR reranking not yet implemented.
    """
    raise NotImplementedError("MMR reranking not yet implemented")


async def keyword_search(
    query: str,
    top_k: int = 10,
    filter_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Full-text search using PostgreSQL tsvector / tsquery.

    Args:
        query: Raw query string (will be converted to tsquery).
        top_k: Maximum number of results to return.
        filter_metadata: Optional metadata filter.

    Returns:
        List of document dicts with keys: id, content, metadata, rank.

    Raises:
        NotImplementedError: Full-text search not yet implemented.
    """
    raise NotImplementedError("Full-text keyword search not yet implemented")
