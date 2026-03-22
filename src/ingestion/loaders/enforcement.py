"""Loader for EnforcementLog signals.

Validates incoming records against EnforcementLog, wraps them in a
SignalEnvelope, and writes them to the raw.enforcement_logs Snowflake table.
Failed records are routed to the dead-letter handler.
"""

from __future__ import annotations

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
        envelope = SignalEnvelope(
            signal_type=SignalType.ENFORCEMENT,
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
    """Write a validated envelope to raw.enforcement_logs.

    Args:
        envelope: The validated signal envelope.

    Raises:
        NotImplementedError: Snowflake write not yet implemented.
    """
    raise NotImplementedError("Snowflake write not yet implemented")
