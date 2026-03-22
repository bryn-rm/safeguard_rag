"""Unit tests for router routing logic (pure functions only, no LLM calls)."""

from __future__ import annotations

import pytest

from src.pipeline.graph import route_after_scoring, route_to_retrieval
from src.pipeline.state import initial_state


class TestRouteToRetrieval:
    """Tests for the route_to_retrieval conditional edge function."""

    def test_sql_strategy_routes_to_retrieval_sql(self) -> None:
        state = initial_state("test query")
        state["retrieval_strategy"] = "sql"
        assert route_to_retrieval(state) == "retrieval_sql"

    def test_vector_strategy_routes_to_retrieval_vector(self) -> None:
        state = initial_state("test query")
        state["retrieval_strategy"] = "vector"
        assert route_to_retrieval(state) == "retrieval_vector"

    def test_keyword_strategy_routes_to_retrieval_keyword(self) -> None:
        state = initial_state("test query")
        state["retrieval_strategy"] = "keyword"
        assert route_to_retrieval(state) == "retrieval_keyword"

    def test_none_strategy_defaults_to_vector(self) -> None:
        state = initial_state("test query")
        state["retrieval_strategy"] = None
        assert route_to_retrieval(state) == "retrieval_vector"

    def test_unknown_strategy_defaults_to_vector(self) -> None:
        state = initial_state("test query")
        state["retrieval_strategy"] = "unknown"
        assert route_to_retrieval(state) == "retrieval_vector"


class TestRouteAfterScoring:
    """Tests for the route_after_scoring conditional edge function."""

    def test_high_confidence_no_retry_returns_end(self) -> None:
        state = initial_state("test query")
        state["confidence_score"] = 0.9
        state["retry_count"] = 0
        state["strategy_history"] = ["sql"]
        assert route_after_scoring(state) == "end"

    def test_low_confidence_with_retries_remaining_returns_retry(self) -> None:
        state = initial_state("test query")
        state["confidence_score"] = 0.2
        state["retry_count"] = 0
        state["strategy_history"] = ["sql"]
        assert route_after_scoring(state) == "retry"

    def test_max_retries_reached_returns_end(self) -> None:
        state = initial_state("test query")
        state["confidence_score"] = 0.2
        state["retry_count"] = 2
        state["strategy_history"] = ["sql", "vector", "keyword"]
        assert route_after_scoring(state) == "end"

    def test_all_strategies_exhausted_returns_end(self) -> None:
        state = initial_state("test query")
        state["confidence_score"] = 0.1
        state["retry_count"] = 1
        state["strategy_history"] = ["sql", "vector", "keyword"]
        assert route_after_scoring(state) == "end"
