"""Unit tests for Pydantic signal schema validation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.ingestion.schemas import (
    ActionType,
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

NOW = datetime.now(tz=UTC)


# ---------------------------------------------------------------------------
# ClassifierOutput
# ---------------------------------------------------------------------------


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

    def test_signal_id_auto_generated(self) -> None:
        obj = ClassifierOutput.model_validate(self._valid())
        assert isinstance(obj.signal_id, uuid.UUID)

    def test_signal_ids_are_unique(self) -> None:
        a = ClassifierOutput.model_validate(self._valid())
        b = ClassifierOutput.model_validate(self._valid())
        assert a.signal_id != b.signal_id

    def test_score_out_of_range_above_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ClassifierOutput.model_validate(self._valid(score=1.5))
        errors = exc_info.value.errors()
        assert any("score" in str(e["loc"]) for e in errors)

    def test_score_out_of_range_below_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ClassifierOutput.model_validate(self._valid(score=-0.01))
        errors = exc_info.value.errors()
        assert any("score" in str(e["loc"]) for e in errors)

    def test_is_positive_inconsistency_raises(self) -> None:
        with pytest.raises(ValidationError, match="is_positive"):
            ClassifierOutput.model_validate(self._valid(score=0.3, is_positive=True))

    def test_is_positive_false_for_low_score(self) -> None:
        obj = ClassifierOutput.model_validate(self._valid(score=0.2, is_positive=False))
        assert obj.is_positive is False

    def test_missing_model_id_raises(self) -> None:
        data = self._valid()
        del data["model_id"]  # type: ignore[misc]
        with pytest.raises(ValidationError) as exc_info:
            ClassifierOutput.model_validate(data)
        assert any("model_id" in str(e["loc"]) for e in exc_info.value.errors())

    def test_missing_entity_id_raises(self) -> None:
        data = self._valid()
        del data["entity_id"]  # type: ignore[misc]
        with pytest.raises(ValidationError) as exc_info:
            ClassifierOutput.model_validate(data)
        assert any("entity_id" in str(e["loc"]) for e in exc_info.value.errors())

    def test_empty_model_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            ClassifierOutput.model_validate(self._valid(model_id=""))

    def test_default_threshold_is_half(self) -> None:
        obj = ClassifierOutput.model_validate(
            {k: v for k, v in self._valid().items() if k != "threshold"}
        )
        assert obj.threshold == 0.5

    def test_metadata_defaults_to_empty_dict(self) -> None:
        obj = ClassifierOutput.model_validate(self._valid())
        assert obj.metadata == {}

    def test_custom_metadata_preserved(self) -> None:
        obj = ClassifierOutput.model_validate(
            self._valid(metadata={"region": "us-east-1", "version": "3.2"})
        )
        assert obj.metadata["region"] == "us-east-1"


# ---------------------------------------------------------------------------
# UserReport
# ---------------------------------------------------------------------------


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
        with pytest.raises(ValidationError) as exc_info:
            UserReport.model_validate(self._valid(report_type="nonexistent_type"))
        assert any("report_type" in str(e["loc"]) for e in exc_info.value.errors())

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UserReport.model_validate(self._valid(severity="extreme"))
        errors = exc_info.value.errors()
        assert any("severity" in str(e["loc"]) for e in errors)

    def test_all_valid_severities_accepted(self) -> None:
        for sev in ("low", "medium", "high", "critical"):
            obj = UserReport.model_validate(self._valid(severity=sev))
            assert obj.severity == ReportSeverity(sev)

    def test_all_valid_report_types_accepted(self) -> None:
        for rt in ("spam", "harassment", "hate_speech", "csam", "self_harm",
                   "misinformation", "other"):
            obj = UserReport.model_validate(self._valid(report_type=rt))
            assert obj.report_type == ReportType(rt)

    def test_missing_reporter_id_raises(self) -> None:
        data = self._valid()
        del data["reporter_id"]  # type: ignore[misc]
        with pytest.raises(ValidationError) as exc_info:
            UserReport.model_validate(data)
        assert any("reporter_id" in str(e["loc"]) for e in exc_info.value.errors())

    def test_empty_description_is_allowed(self) -> None:
        obj = UserReport.model_validate(self._valid(description=""))
        assert obj.description == ""

    def test_default_status_is_pending(self) -> None:
        data = {k: v for k, v in self._valid().items() if k != "status"}
        obj = UserReport.model_validate(data)
        assert obj.status == ReportStatus.PENDING

    def test_default_severity_is_medium(self) -> None:
        data = {k: v for k, v in self._valid().items() if k != "severity"}
        obj = UserReport.model_validate(data)
        assert obj.severity == ReportSeverity.MEDIUM


# ---------------------------------------------------------------------------
# EnforcementLog
# ---------------------------------------------------------------------------


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
        assert obj.action_type == ActionType.BAN

    def test_empty_reason_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            EnforcementLog.model_validate(self._valid(reason=""))
        assert any("reason" in str(e["loc"]) for e in exc_info.value.errors())

    def test_invalid_action_type_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            EnforcementLog.model_validate(self._valid(action_type="delete_account"))
        assert any("action_type" in str(e["loc"]) for e in exc_info.value.errors())

    def test_all_valid_action_types_accepted(self) -> None:
        for at in ("warn", "suspend", "ban", "content_removal", "shadowban", "escalate"):
            obj = EnforcementLog.model_validate(self._valid(action_type=at))
            assert obj.action_type == ActionType(at)

    def test_missing_policy_id_raises(self) -> None:
        data = self._valid()
        del data["policy_id"]  # type: ignore[misc]
        with pytest.raises(ValidationError) as exc_info:
            EnforcementLog.model_validate(data)
        assert any("policy_id" in str(e["loc"]) for e in exc_info.value.errors())

    def test_action_id_auto_generated(self) -> None:
        obj = EnforcementLog.model_validate(self._valid())
        assert isinstance(obj.action_id, uuid.UUID)


# ---------------------------------------------------------------------------
# ModelOutput
# ---------------------------------------------------------------------------


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
        with pytest.raises(ValidationError) as exc_info:
            ModelOutput.model_validate(self._valid(prompt_hash="notahash"))
        assert any("prompt_hash" in str(e["loc"]) for e in exc_info.value.errors())

    def test_prompt_hash_wrong_length_raises(self) -> None:
        with pytest.raises(ValidationError):
            ModelOutput.model_validate(self._valid(prompt_hash="abc123"))

    def test_safety_label_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ModelOutput.model_validate(self._valid(safety_labels={"toxicity": 1.5}))
        assert any("safety_labels" in str(e["loc"]) for e in exc_info.value.errors())

    def test_safety_label_below_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            ModelOutput.model_validate(self._valid(safety_labels={"toxicity": -0.1}))

    def test_negative_latency_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ModelOutput.model_validate(self._valid(latency_ms=-1))
        assert any("latency_ms" in str(e["loc"]) for e in exc_info.value.errors())

    def test_empty_safety_labels_allowed(self) -> None:
        obj = ModelOutput.model_validate(self._valid(safety_labels={}))
        assert obj.safety_labels == {}

    def test_multiple_safety_labels_accepted(self) -> None:
        labels = {"toxicity": 0.02, "self_harm": 0.01, "pii": 0.0, "prompt_injection": 0.95}
        obj = ModelOutput.model_validate(self._valid(safety_labels=labels))
        assert obj.safety_labels["prompt_injection"] == pytest.approx(0.95)

    def test_missing_output_text_raises(self) -> None:
        data = self._valid()
        del data["output_text"]  # type: ignore[misc]
        with pytest.raises(ValidationError) as exc_info:
            ModelOutput.model_validate(data)
        assert any("output_text" in str(e["loc"]) for e in exc_info.value.errors())


# ---------------------------------------------------------------------------
# SignalEnvelope
# ---------------------------------------------------------------------------


class TestSignalEnvelope:
    """Tests for SignalEnvelope wrapper — field preservation and type checking."""

    def _classifier_payload(self) -> ClassifierOutput:
        return ClassifierOutput(
            model_id="toxicity-v3",
            entity_id="content-001",
            label="toxic",
            score=0.87,
            threshold=0.5,
            is_positive=True,
            timestamp=NOW,
        )

    def _report_payload(self) -> UserReport:
        return UserReport(
            reporter_id="user-001",
            reported_entity_id="content-xyz",
            report_type=ReportType.HARASSMENT,
            description="Harassment",
            severity=ReportSeverity.HIGH,
            status=ReportStatus.PENDING,
            timestamp=NOW,
        )

    def test_classifier_envelope_preserves_all_fields(self) -> None:
        payload = self._classifier_payload()
        env = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER,
            payload=payload,
            source="test-source",
            ingested_at=NOW,
        )
        assert env.signal_type == SignalType.CLASSIFIER
        assert env.source == "test-source"
        assert env.ingested_at == NOW
        assert env.loaded_at is None
        assert isinstance(env.envelope_id, uuid.UUID)
        assert isinstance(env.payload, ClassifierOutput)
        assert env.payload.label == "toxic"
        assert env.payload.score == pytest.approx(0.87)

    def test_report_envelope_preserves_all_fields(self) -> None:
        payload = self._report_payload()
        env = SignalEnvelope(
            signal_type=SignalType.REPORT,
            payload=payload,
            source="report-system",
            ingested_at=NOW,
        )
        assert env.signal_type == SignalType.REPORT
        assert isinstance(env.payload, UserReport)
        assert env.payload.report_type == ReportType.HARASSMENT

    def test_mismatched_payload_type_raises(self) -> None:
        """A UserReport payload with signal_type=CLASSIFIER must fail."""
        payload = self._report_payload()
        with pytest.raises(ValidationError, match="requires"):
            SignalEnvelope(
                signal_type=SignalType.CLASSIFIER,
                payload=payload,  # type: ignore[arg-type]
                source="test",
                ingested_at=NOW,
            )

    def test_envelope_ids_are_unique(self) -> None:
        payload = self._classifier_payload()
        env_a = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER, payload=payload,
            source="s", ingested_at=NOW,
        )
        env_b = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER, payload=payload,
            source="s", ingested_at=NOW,
        )
        assert env_a.envelope_id != env_b.envelope_id

    def test_loaded_at_can_be_set(self) -> None:
        payload = self._classifier_payload()
        env = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER,
            payload=payload,
            source="test",
            ingested_at=NOW,
            loaded_at=NOW,
        )
        assert env.loaded_at == NOW

    def test_envelope_round_trips_json(self) -> None:
        payload = self._classifier_payload()
        env = SignalEnvelope(
            signal_type=SignalType.CLASSIFIER,
            payload=payload,
            source="test",
            ingested_at=NOW,
        )
        json_str = env.model_dump_json()
        assert "toxicity-v3" in json_str
        assert "classifier" in json_str

    def test_all_four_signal_types_wrap_correctly(self) -> None:
        enforcement = EnforcementLog(
            entity_id="e1", action_type=ActionType.WARN,
            policy_id="p1", enforced_by="auto", reason="test", timestamp=NOW,
        )
        model_out = ModelOutput(
            model_id="claude-sonnet-4-6",
            prompt_hash="a" * 64,
            output_text="safe",
            timestamp=NOW,
        )
        for sig_type, payload in [
            (SignalType.ENFORCEMENT, enforcement),
            (SignalType.MODEL_OUTPUT, model_out),
        ]:
            env = SignalEnvelope(
                signal_type=sig_type, payload=payload,
                source="test", ingested_at=NOW,
            )
            assert env.signal_type == sig_type
