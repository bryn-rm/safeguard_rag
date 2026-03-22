"""Streamlit dashboard for safeguards-RAG observability.

Charts:
  - Signal volume time series
  - Retrieval strategy distribution (pie)
  - Confidence score histogram
  - Retry rate trend
  - Data freshness gauges

Run with: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.charts import (
    confidence_histogram,
    freshness_gauges,
    retry_rate_trend,
    signal_volume_chart,
    strategy_distribution_pie,
)


def main() -> None:
    """Entry point for the Streamlit dashboard."""
    st.set_page_config(
        page_title="Safeguards RAG",
        page_icon=":shield:",
        layout="wide",
    )
    st.title("Safeguards RAG — Observability Dashboard")

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Signals (24h)", "—", help="Total signals ingested in last 24 hours")
    col2.metric("Avg Confidence", "—", help="Mean confidence score across recent pipeline runs")
    col3.metric("Retry Rate", "—", help="Fraction of runs that required at least one retry")
    col4.metric("Dead Letters (24h)", "—", help="Ingestion failures in last 24 hours")

    st.divider()

    # Charts — left column
    left, right = st.columns(2)
    with left:
        st.subheader("Signal Volume")
        signal_volume_chart()

        st.subheader("Confidence Score Distribution")
        confidence_histogram()

    with right:
        st.subheader("Retrieval Strategy Distribution")
        strategy_distribution_pie()

        st.subheader("Retry Rate Trend")
        retry_rate_trend()

    st.divider()
    st.subheader("Data Freshness")
    freshness_gauges()


if __name__ == "__main__":
    main()
