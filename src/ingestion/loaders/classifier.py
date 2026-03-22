"""Loader for ClassifierOutput signals.

Validates incoming records against ClassifierOutput, wraps them in a
SignalEnvelope, and returns them for downstream persistence. Failed records
are routed to the dead-letter handler.
"""

from __future__ import annotations

import asyncio
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
    except ValidationError as exc:
        dead = build_dead_letter(raw, exc, source)
        await write_dead_letter(dead)
        return None

    return SignalEnvelope(
        signal_type=SignalType.CLASSIFIER,
        payload=payload,
        source=source,
        ingested_at=datetime.now(tz=UTC),
    )


async def load_batch(
    records: list[dict[str, Any]],
    source: str = "classifier-pipeline",
) -> tuple[list[SignalEnvelope], int]:
    """Validate and load a batch of classifier output records concurrently.

    Args:
        records: List of raw dicts from the upstream classifier system.
        source: Identifier of the originating system.

    Returns:
        A tuple of (valid_envelopes, failure_count). Failed records are
        written to dead letters; they do not appear in valid_envelopes.
    """
    results = await asyncio.gather(
        *[load_classifier_output(r, source) for r in records]
    )
    valid = [e for e in results if e is not None]
    return valid, len(records) - len(valid)
