"""Embedding logic for vector retrieval.

Wraps OpenAI text-embedding-3-small (or Cohere) to produce dense vectors
for queries and documents. Supports batched async embedding.
"""

from __future__ import annotations

import numpy as np


async def embed_query(text: str) -> list[float]:
    """Embed a single query string.

    Args:
        text: The query string to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        NotImplementedError: Embedding API call not yet implemented.
    """
    raise NotImplementedError("Embedding API call not yet implemented")


async def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document strings.

    Args:
        texts: List of document strings to embed.

    Returns:
        A list of embedding vectors, one per input text.

    Raises:
        NotImplementedError: Batch embedding not yet implemented.
    """
    raise NotImplementedError("Batch embedding not yet implemented")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Cosine similarity in [-1, 1].
    """
    vec_a = np.array(a, dtype=np.float64)
    vec_b = np.array(b, dtype=np.float64)
    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
