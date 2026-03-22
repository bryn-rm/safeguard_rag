"""Synthesiser node: produces a grounded natural-language answer.

Sends the query and retrieved_context to Claude Sonnet with a chain-of-thought
prompt that instructs it to cite retrieved evidence and avoid hallucination.
Returns the answer as synthesised_answer.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


async def synthesiser_node(state: PipelineState) -> dict[str, Any]:
    """Generate a grounded answer from the retrieved context.

    The prompt instructs the model to:
      1. Only assert claims supported by retrieved_context.
      2. Cite the source of each claim (row index or document ID).
      3. Flag uncertainty explicitly rather than guessing.

    Args:
        state: Current pipeline state. Uses query and retrieved_context.

    Returns:
        State patch with key: synthesised_answer.

    Raises:
        NotImplementedError: LLM call not yet implemented.
    """
    raise NotImplementedError("Synthesiser LLM call not yet implemented")
