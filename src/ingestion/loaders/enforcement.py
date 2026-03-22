"""Loader for EnforcementLog signals.

Validates incoming records against EnforcementLog, wraps them in a
SignalEnvelope, and returns them for downstream persistence. Failed records
are routed to the dead-letter handler.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.ingestion.dead_letter import build_dead_letter, write_dead_letter
from src.ingestion.schemas import EnforcementLog, SignalEnvelope, SignalType


async def load_enforcement_log(
    raw: dict[str, Any],
    source: str = "enforcement-system",
) -> SignalEnvelope | None:
    """Validate and load a single enforcement log record.

    Args:
        raw: Raw dict from the enforcement system.
        source: Identifier of the originating system.

    Returns:
        A validated SignalEnvelope on success, or None if validation fails.
    """
    try:
        payload = EnforcementLog.model_validate(raw)
    except ValidationError as exc:
        dead = build_dead_letter(raw, exc, source)
        await write_dead_letter(dead)
        return None

    return SignalEnvelope(
        signal_type=SignalType.ENFORCEMENT,
        payload=payload,
        source=source,
        ingested_at=datetime.now(tz=UTC),
    )


async def load_batch(
    records: list[dict[str, Any]],
    source: str = "enforcement-system",
) -> tuple[list[SignalEnvelope], int]:
    """Validate and load a batch of enforcement log records concurrently.

    Args:
        records: List of raw dicts from the enforcement system.
        source: Identifier of the originating system.

    Returns:
        A tuple of (valid_envelopes, failure_count).
    """
    results = await asyncio.gather(
        *[load_enforcement_log(r, source) for r in records]
    )
    valid = [e for e in results if e is not None]
    return valid, len(records) - len(valid)
