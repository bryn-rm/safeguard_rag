"""Reusable Streamlit chart components for the safeguards-RAG dashboard.

Each function renders one chart section. No custom CSS — uses only Streamlit
native components and st.metric for KPIs.
"""

from __future__ import annotations

import streamlit as st


def signal_volume_chart() -> None:
    """Render a time-series chart of signal volume by type.

    Data is fetched from Snowflake fct_signals. Placeholder until
    Snowflake connection is implemented.
    """
    st.info("Signal volume chart: Snowflake connection not yet implemented.")


def strategy_distribution_pie() -> None:
    """Render a pie chart of retrieval strategy usage.

    Shows the proportion of pipeline runs using SQL, vector, and keyword
    retrieval strategies.
    """
    st.info("Strategy distribution chart: data source not yet connected.")


def confidence_histogram() -> None:
    """Render a histogram of confidence scores across recent pipeline runs.

    Sourced from LangSmith trace metadata. Placeholder until LangSmith
    integration is implemented.
    """
    st.info("Confidence histogram: LangSmith integration not yet implemented.")


def retry_rate_trend() -> None:
    """Render a line chart showing retry rate over time.

    A run is counted as retried if retry_count > 0 in LangSmith metadata.
    """
    st.info("Retry rate trend: LangSmith integration not yet implemented.")


def freshness_gauges() -> None:
    """Render freshness gauges for each signal type.

    Shows time since last ingestion vs. configured freshness window.
    Green = fresh, Red = stale.
    """
    signal_types = ["classifier", "report", "enforcement", "model_output"]
    cols = st.columns(len(signal_types))
    for col, sig_type in zip(cols, signal_types, strict=False):
        with col:
            col.metric(
                label=sig_type.replace("_", " ").title(),
                value="—",
                help=f"Minutes since last {sig_type} signal",
            )
