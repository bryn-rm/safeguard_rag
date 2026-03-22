"""Unit tests for Pydantic signal schema validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.ingestion.schemas import (
    ClassifierOutput,
    DeadLetter,
    EnforcementLog,
    ModelOutput,
    ReportSeverity,
    ReportStatus,
    ReportType,
    SignalEnvelope,
    SignalType,
    UserReport,
)

NOW = datetime.now(tz=timezone.utc)


class TestClassifierOutput:
    """Tests for ClassifierOutput validation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "model_id": "toxicity-v3",
            "entity_id": "content-001",
            "label": "toxic",
            "score": 0.8,
            "threshold": 0.5,
            "is_positive": True,
            "timestamp": NOW,
        }
        base.update(overrides)
        return base

    def test_valid_record_parses(self) -> None:
        obj = ClassifierOutput.model_validate(self._valid())
        assert obj.label == "toxic"
        assert obj.is_positive is True

    def test_is_positive_inconsistency_raises(self) -> None:
        with pytest.raises(ValidationError, match="is_positive"):
            ClassifierOutput.model_validate(self._valid(score=0.3, is_positive=True))

    def test_score_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            ClassifierOutput.model_validate(self._valid(score=1.5))

    def test_signal_id_auto_generated(self) -> None:
        obj = ClassifierOutput.model_validate(self._valid())
        assert isinstance(obj.signal_id, uuid.UUID)


class TestUserReport:
    """Tests for UserReport validation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "reporter_id": "user-001",
            "reported_entity_id": "content-xyz",
            "report_type": "harassment",
            "description": "  Offensive content  ",
            "severity": "high",
            "status": "pending",
            "timestamp": NOW,
        }
        base.update(overrides)
        return base

    def test_valid_report_parses(self) -> None:
        obj = UserReport.model_validate(self._valid())
        assert obj.report_type == ReportType.HARASSMENT

    def test_description_is_stripped(self) -> None:
        obj = UserReport.model_validate(self._valid())
        assert obj.description == "Offensive content"

    def test_invalid_report_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserReport.model_validate(self._valid(report_type="nonexistent_type"))


class TestEnforcementLog:
    """Tests for EnforcementLog validation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "entity_id": "user-bad",
            "action_type": "ban",
            "policy_id": "policy-tos-v2",
            "enforced_by": "auto-enforcer",
            "reason": "Repeated violations",
            "timestamp": NOW,
        }
        base.update(overrides)
        return base

    def test_valid_enforcement_log_parses(self) -> None:
        obj = EnforcementLog.model_validate(self._valid())
        assert obj.action_type.value == "ban"

    def test_empty_reason_raises(self) -> None:
        with pytest.raises(ValidationError):
            EnforcementLog.model_validate(self._valid(reason=""))


class TestModelOutput:
    """Tests for ModelOutput validation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "model_id": "claude-sonnet-4-6",
            "prompt_hash": "a" * 64,
            "output_text": "Here is a safe answer.",
            "safety_labels": {"toxicity": 0.01},
            "latency_ms": 300,
            "timestamp": NOW,
        }
        base.update(overrides)
        return base

    def test_valid_model_output_parses(self) -> None:
        obj = ModelOutput.model_validate(self._valid())
        assert obj.latency_ms == 300

    def test_invalid_prompt_hash_raises(self) -> None:
        with pytest.raises(ValidationError):
            ModelOutput.model_validate(self._valid(prompt_hash="notahash"))

    def test_safety_label_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            ModelOutput.model_validate(self._valid(safety_labels={"toxicity": 1.5}))
