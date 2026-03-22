"""Dead-letter handler for failed ingestion records.

Invalid records that fail Pydantic validation are written to
data/dead_letters.jsonl with structured error context. The file is
append-only. Use get_dead_letter_stats() to summarise failures by type.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.ingestion.schemas import DeadLetter

DEAD_LETTER_PATH = Path("data/dead_letters.jsonl")


def build_dead_letter(
    raw_payload: dict[str, Any],
    exc: Exception,
    source: str,
) -> DeadLetter:
    """Construct a DeadLetter record from a failed validation exception.

    Extracts structured field-level error details when exc is a Pydantic
    ValidationError; falls back to a single error entry otherwise.

    Args:
        raw_payload: The original dict that failed validation.
        exc: The exception raised during validation.
        source: Originating system identifier.

    Returns:
        A DeadLetter model ready for persistence.
    """
    if isinstance(exc, ValidationError):
        error_details: list[dict[str, Any]] = [
            {
                "field": " -> ".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
                "input": err.get("input"),
            }
            for err in exc.errors()
        ]
    else:
        error_details = [{"field": "unknown", "message": str(exc), "type": type(exc).__name__}]

    return DeadLetter(
        raw_payload=raw_payload,
        error_type=type(exc).__name__,
        error_message=str(exc),
        error_details=error_details,
        source=source,
        failed_at=datetime.now(tz=UTC),
    )


async def write_dead_letter(dead_letter: DeadLetter) -> None:
    """Persist a dead-letter record to data/dead_letters.jsonl.

    Creates the data/ directory if it does not exist. Appends one JSON
    line per record so the file is streamable and append-safe.

    Args:
        dead_letter: The dead-letter record to persist.
    """
    DEAD_LETTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DEAD_LETTER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(dead_letter.model_dump_json() + "\n")


def get_dead_letter_stats() -> dict[str, int]:
    """Return failure counts grouped by error_type from the dead-letter file.

    Reads the full JSONL file on each call — suitable for CLI/dashboard use,
    not for hot paths.

    Returns:
        Dict mapping error_type strings to occurrence counts. Returns an
        empty dict if the dead-letter file does not exist.
    """
    if not DEAD_LETTER_PATH.exists():
        return {}

    counts: dict[str, int] = {}
    with DEAD_LETTER_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                error_type: str = record.get("error_type", "unknown")
                counts[error_type] = counts.get(error_type, 0) + 1
            except json.JSONDecodeError:
                counts["_malformed_line"] = counts.get("_malformed_line", 0) + 1

    return counts
