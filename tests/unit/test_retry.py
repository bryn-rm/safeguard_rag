"""Unit tests for the retry controller."""

from __future__ import annotations

from src.pipeline.retry import increment_retry, next_strategy, should_retry
from src.pipeline.state import initial_state


class TestShouldRetry:
    """Tests for should_retry()."""

    def test_low_confidence_below_threshold_returns_true(self) -> None:
        state = initial_state("q")
        state["confidence_score"] = 0.3
        state["retry_count"] = 0
        assert should_retry(state, confidence_threshold=0.5) is True

    def test_high_confidence_returns_false(self) -> None:
        state = initial_state("q")
        state["confidence_score"] = 0.8
        state["retry_count"] = 0
        assert should_retry(state, confidence_threshold=0.5) is False

    def test_max_retries_reached_returns_false(self) -> None:
        state = initial_state("q")
        state["confidence_score"] = 0.1
        state["retry_count"] = 2
        assert should_retry(state) is False

    def test_none_confidence_returns_true(self) -> None:
        state = initial_state("q")
        state["confidence_score"] = None
        state["retry_count"] = 0
        assert should_retry(state) is True


class TestNextStrategy:
    """Tests for next_strategy()."""

    def test_returns_first_untried_strategy(self) -> None:
        state = initial_state("q")
        state["strategy_history"] = []
        assert next_strategy(state) == "sql"

    def test_skips_tried_strategies(self) -> None:
        state = initial_state("q")
        state["strategy_history"] = ["sql"]
        assert next_strategy(state) == "vector"

    def test_returns_none_when_all_exhausted(self) -> None:
        state = initial_state("q")
        state["strategy_history"] = ["sql", "vector", "keyword"]
        assert next_strategy(state) is None


class TestIncrementRetry:
    """Tests for increment_retry()."""

    def test_increments_retry_count(self) -> None:
        state = initial_state("q")
        state["retry_count"] = 1
        patch = increment_retry(state)
        assert patch["retry_count"] == 2

    def test_clears_stale_fields(self) -> None:
        state = initial_state("q")
        state["synthesised_answer"] = "old answer"
        state["confidence_score"] = 0.3
        patch = increment_retry(state)
        assert patch["synthesised_answer"] is None
        assert patch["confidence_score"] is None
        assert patch["retrieved_context"] == []
