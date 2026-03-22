"""Alerting for data quality and freshness failures.

Sends structured alerts when GE checkpoints fail or freshness windows expire.
"""

from __future__ import annotations

from typing import Any


async def send_freshness_alert(freshness_result: dict[str, Any]) -> None:
    """Send an alert for a stale signal type.

    Args:
        freshness_result: Result dict from freshness.check_freshness().

    Raises:
        NotImplementedError: Alert dispatch not yet implemented.
    """
    raise NotImplementedError("Alert dispatch not yet implemented")


async def send_quality_alert(validation_result: dict[str, Any]) -> None:
    """Send an alert when a Great Expectations checkpoint fails.

    Args:
        validation_result: Result dict from expectations.run_checkpoint().

    Raises:
        NotImplementedError: Alert dispatch not yet implemented.
    """
    raise NotImplementedError("Alert dispatch not yet implemented")
