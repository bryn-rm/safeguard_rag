"""Dead-letter handler for failed ingestion records.

Invalid records that fail Pydantic validation are written to raw.dead_letters
in Snowflake with structured error context. The table is append-only.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.ingestion.schemas import DeadLetter


def build_dead_letter(
    raw_payload: dict[str, Any],
    exc: Exception,
    source: str,
) -> DeadLetter:
    """Construct a DeadLetter record from a failed validation exception.

    Args:
        raw_payload: The original dict that failed validation.
        exc: The exception raised during validation.
        source: Originating system identifier.

    Returns:
        A DeadLetter model ready for persistence.
    """
    return DeadLetter(
        raw_payload=raw_payload,
        error_type=type(exc).__name__,
        error_message=str(exc),
        source=source,
        failed_at=datetime.now(tz=UTC),
    )


async def write_dead_letter(dead_letter: DeadLetter) -> None:
    """Persist a dead-letter record to raw.dead_letters in Snowflake.

    Args:
        dead_letter: The dead-letter record to persist.

    Raises:
        NotImplementedError: Snowflake write not yet implemented.
    """
    raise NotImplementedError("Snowflake dead-letter write not yet implemented")
