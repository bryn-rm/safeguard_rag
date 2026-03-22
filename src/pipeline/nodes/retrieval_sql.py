"""SQL retrieval node: executes a Jinja2 SQL template against Snowflake.

Selects the appropriate template from the registry based on signal_type and
query intent, renders it with safe parameterisation, runs it against
Snowflake, and returns the rows as retrieved_context.
"""

from __future__ import annotations

from typing import Any

from src.pipeline.state import PipelineState


async def retrieval_sql_node(state: PipelineState) -> dict[str, Any]:
    """Execute a Snowflake SQL query and return rows as retrieved context.

    Template selection is driven by state["router_output"]. Parameters are
    type-checked against the registry before rendering. Results are returned
    as a list of row dicts, each with a "source" key set to "sql".

    Args:
        state: Current pipeline state. Uses router_output and signal_type.

    Returns:
        State patch with keys: retrieved_context, retrieval_strategy.

    Raises:
        NotImplementedError: Snowflake connection not yet implemented.
    """
    raise NotImplementedError("SQL retrieval not yet implemented")
