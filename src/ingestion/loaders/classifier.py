"""Loader for ClassifierOutput signals.

Validates incoming records against ClassifierOutput, wraps them in a
SignalEnvelope, and writes them to the raw.classifier_outputs Snowflake table.
Failed records are routed to the dead-letter handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.ingestion.dead_letter import build_dead_letter, write_dead_letter
from src.ingestion.schemas import ClassifierOutput, SignalEnvelope, SignalType


async def load_classifier_output(
    raw: dict[str, Any],
    source: str = "classifier-pipeline",
) -> SignalEnvelope | None:
    """Validate and load a single classifier output record.

    Args:
        raw: Raw dict from the upstream classifier system.
        source: Identifier of the originating system.

    Returns:
        A validated SignalEnvelope on success, or None if validation fails
        (the failed record is written to dead letters).
    """
    try:
        payload = ClassifierOutput.model_validate(raw)
        envelope = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER,
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
    """Write a validated envelope to raw.classifier_outputs.

    Args:
        envelope: The validated signal envelope.

    Raises:
        NotImplementedError: Snowflake write not yet implemented.
    """
    raise NotImplementedError("Snowflake write not yet implemented")
