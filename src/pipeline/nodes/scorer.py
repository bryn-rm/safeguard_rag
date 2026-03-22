"""Scorer node: self-evaluates answer confidence.

Uses Claude Sonnet to assess how well the synthesised_answer is grounded in
retrieved_context. Returns a float confidence_score in [0, 1].

WARNING: This prompt is the most sensitive component. Small wording changes
can shift score distributions significantly. Always run the regression suite
after editing.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


async def scorer_node(state: PipelineState) -> dict[str, Any]:
    """Self-evaluate the synthesised answer and return a confidence score.

    The scoring prompt asks the LLM to assess:
      - Faithfulness: is every claim backed by the retrieved context?
      - Completeness: does the answer address the full query?
      - Uncertainty: are gaps or unknowns acknowledged?

    The LLM returns a JSON object with fields {score: float, rationale: str}.
    score is extracted and stored as confidence_score.

    Args:
        state: Current pipeline state. Uses query, retrieved_context, and
            synthesised_answer.

    Returns:
        State patch with key: confidence_score.

    Raises:
        NotImplementedError: LLM call not yet implemented.
    """
    raise NotImplementedError("Scorer LLM call not yet implemented")
