"""Signal freshness checks.

Fires alerts if no new signals arrive within the configured window:
  - classifiers: 15 minutes (default)
  - reports: 60 minutes (default)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DEFAULT_FRESHNESS_WINDOWS: dict[str, int] = {
    "classifier": 15,
    "report": 60,
    "enforcement": 60,
    "model_output": 30,
}


async def get_latest_signal_timestamp(signal_type: str) -> datetime | None:
    """Query Snowflake for the most recent _loaded_at for the given signal type.

    Args:
        signal_type: One of "classifier", "report", "enforcement", "model_output".

    Returns:
        UTC datetime of the most recent load, or None if no records exist.

    Raises:
        NotImplementedError: Snowflake query not yet implemented.
    """
    raise NotImplementedError("Snowflake freshness query not yet implemented")


async def check_freshness(
    signal_type: str,
    window_minutes: int | None = None,
) -> dict[str, Any]:
    """Check whether fresh signals have arrived within the configured window.

    Args:
        signal_type: Signal category to check.
        window_minutes: Override the default freshness window (minutes).

    Returns:
        Dict with keys: signal_type, is_fresh, latest_timestamp,
            window_minutes, checked_at.
    """
    window = window_minutes or DEFAULT_FRESHNESS_WINDOWS.get(signal_type, 60)
    now = datetime.now(tz=UTC)
    latest = await get_latest_signal_timestamp(signal_type)
    is_fresh = latest is not None and (now - latest) <= timedelta(minutes=window)
    return {
        "signal_type": signal_type,
        "is_fresh": is_fresh,
        "latest_timestamp": latest,
        "window_minutes": window,
        "checked_at": now,
    }
