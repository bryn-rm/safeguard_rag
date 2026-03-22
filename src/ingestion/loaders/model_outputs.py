"""Loader for ModelOutput signals.

Validates incoming records against ModelOutput, wraps them in a SignalEnvelope,
and writes them to the raw.model_outputs Snowflake table. Failed records are
routed to the dead-letter handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.ingestion.dead_letter import build_dead_letter, write_dead_letter
from src.ingestion.schemas import ModelOutput, SignalEnvelope, SignalType


async def load_model_output(
    raw: dict[str, Any],
    source: str = "model-serving",
) -> SignalEnvelope | None:
    """Validate and load a single model output record.

    Args:
        raw: Raw dict from the model serving layer.
        source: Identifier of the originating system.

    Returns:
        A validated SignalEnvelope on success, or None if validation fails.
    """
    try:
        payload = ModelOutput.model_validate(raw)
        envelope = SignalEnvelope(
            signal_type=SignalType.MODEL_OUTPUT,
            payload=payload,
            source=source,
            ingested_at=datetime.now(tz=UTC),
        )
        await _write_to_snowflake(envelope)
        return envelope
    except (ValidationError, Exception) as exc:
        dead = build_dead_letter(raw, exc, source)
        await write_dead_letter(dead)
        return None


async def _write_to_snowflake(envelope: SignalEnvelope) -> None:
    """Write a validated envelope to raw.model_outputs.

    Args:
        envelope: The validated signal envelope.

    Raises:
        NotImplementedError: Snowflake write not yet implemented.
    """
    raise NotImplementedError("Snowflake write not yet implemented")
