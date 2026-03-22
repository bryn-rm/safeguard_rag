"""Integration tests for the end-to-end pipeline.

These tests run against a test Snowflake schema. Skipped in CI unless
SNOWFLAKE_ACCOUNT is set in the environment.
"""

from __future__ import annotations

import os

import pytest

from src.pipeline.state import initial_state


@pytest.mark.skipif(
    not os.environ.get("SNOWFLAKE_ACCOUNT"),
    reason="Snowflake credentials not configured",
)
class TestPipelineIntegration:
    """End-to-end pipeline tests against a real Snowflake test schema."""

    async def test_full_pipeline_run_produces_answer(self) -> None:
        """A full pipeline run should produce a synthesised answer.

        Raises:
            NotImplementedError: Pipeline not yet implemented.
        """
        raise NotImplementedError("Integration test not yet implemented")
