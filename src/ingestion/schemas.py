"""Pydantic v2 signal models for ingestion validation.

Each signal type has its own model. All models are wrapped in SignalEnvelope,
which carries routing metadata. Invalid envelopes are routed to dead letters.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SignalType(StrEnum):
    """Top-level signal categories ingested by the pipeline."""

    CLASSIFIER = "classifier"
    REPORT = "report"
    ENFORCEMENT = "enforcement"
    MODEL_OUTPUT = "model_output"


class ReportType(StrEnum):
    """Taxonomy of user report categories."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    CSAM = "csam"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class ReportSeverity(StrEnum):
    """Severity tiers for user reports."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus(StrEnum):
    """Review lifecycle status for user reports."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ActionType(StrEnum):
    """Enforcement action types."""

    WARN = "warn"
    SUSPEND = "suspend"
    BAN = "ban"
    CONTENT_REMOVAL = "content_removal"
    SHADOWBAN = "shadowban"
    ESCALATE = "escalate"


# ---------------------------------------------------------------------------
# Signal models
# ---------------------------------------------------------------------------


class ClassifierOutput(BaseModel):
    """Output record from a safety classifier model.

    Attributes:
        signal_id: Unique identifier for this classifier output record.
        model_id: Identifier of the classifier model that produced this output.
        entity_id: Identifier of the content or user that was classified.
        label: Predicted safety label (e.g. "toxic", "safe", "spam").
        score: Raw probability score in [0.0, 1.0].
        threshold: Decision threshold used to derive is_positive.
        is_positive: Whether score >= threshold (positive safety signal).
        timestamp: UTC timestamp when the classifier ran.
        metadata: Arbitrary additional fields (model version, feature flags, etc.).
    """

    signal_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_id: str = Field(..., min_length=1, description="Classifier model identifier")
    entity_id: str = Field(..., min_length=1, description="Classified entity identifier")
    label: str = Field(..., min_length=1, description="Predicted safety label")
    score: Annotated[float, Field(ge=0.0, le=1.0, description="Probability score in [0.0, 1.0]")]
    threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    is_positive: bool = Field(..., description="True when score >= threshold")
    timestamp: datetime = Field(..., description="UTC timestamp of classification")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_score_range(self) -> ClassifierOutput:
        """Validate that score is strictly within [0.0, 1.0].

        Field-level ge/le constraints handle this, but this validator provides
        a clearer error message referencing the field name explicitly.
        """
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"score={self.score} is outside the valid range [0.0, 1.0]. "
                "Classifier scores must be probabilities."
            )
        return self

    @model_validator(mode="after")
    def check_is_positive_consistent(self) -> ClassifierOutput:
        """Validate that is_positive matches score vs threshold."""
        expected = self.score >= self.threshold
        if self.is_positive != expected:
            raise ValueError(
                f"is_positive={self.is_positive} is inconsistent with "
                f"score={self.score} and threshold={self.threshold}. "
                f"Expected is_positive={expected}."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model_id": "toxicity-v3",
                    "entity_id": "content-abc123",
                    "label": "toxic",
                    "score": 0.87,
                    "threshold": 0.5,
                    "is_positive": True,
                    "timestamp": "2026-03-22T10:00:00Z",
                    "metadata": {"model_version": "3.2.1", "region": "us-west-2"},
                },
                {
                    "model_id": "pii-detector-v1",
                    "entity_id": "content-def456",
                    "label": "clean",
                    "score": 0.12,
                    "threshold": 0.5,
                    "is_positive": False,
                    "timestamp": "2026-03-22T10:05:00Z",
                    "metadata": {},
                },
            ]
        }
    }


class UserReport(BaseModel):
    """A report submitted by a user about content or another user.

    Attributes:
        report_id: Unique identifier for this report.
        reporter_id: Identifier of the user who filed the report.
        reported_entity_id: Identifier of the reported content or user.
        report_type: Category of the report.
        description: Free-text description provided by the reporter.
        severity: Assessed severity tier (low | medium | high | critical).
        status: Current lifecycle status of the report.
        timestamp: UTC timestamp when the report was submitted.
        metadata: Arbitrary additional fields.
    """

    report_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    reporter_id: str = Field(..., min_length=1)
    reported_entity_id: str = Field(..., min_length=1)
    report_type: ReportType
    description: str = Field(default="", max_length=10_000)
    severity: ReportSeverity = ReportSeverity.MEDIUM
    status: ReportStatus = ReportStatus.PENDING
    timestamp: datetime = Field(..., description="UTC submission timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        """Strip leading/trailing whitespace from the description."""
        return v.strip()

    @model_validator(mode="after")
    def check_severity_valid(self) -> UserReport:
        """Validate that severity is one of low, medium, high, critical.

        The ReportSeverity StrEnum enforces this at parse time, but this
        validator surfaces a clear, field-specific message on failure.
        """
        valid = {s.value for s in ReportSeverity}
        if self.severity not in valid:
            raise ValueError(
                f"severity={self.severity!r} is not valid. "
                f"Must be one of: {sorted(valid)}."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reporter_id": "user-001",
                    "reported_entity_id": "content-xyz",
                    "report_type": "harassment",
                    "description": "This content targets me personally.",
                    "severity": "high",
                    "status": "pending",
                    "timestamp": "2026-03-22T09:30:00Z",
                    "metadata": {"platform": "mobile", "locale": "en-US"},
                },
                {
                    "reporter_id": "user-002",
                    "reported_entity_id": "user-spammer",
                    "report_type": "spam",
                    "description": "Sending unsolicited commercial messages.",
                    "severity": "low",
                    "status": "pending",
                    "timestamp": "2026-03-22T10:15:00Z",
                    "metadata": {},
                },
            ]
        }
    }


class EnforcementLog(BaseModel):
    """A record of an enforcement action taken against an entity.

    Attributes:
        action_id: Unique identifier for this enforcement action.
        entity_id: Identifier of the entity against which action was taken.
        action_type: The type of enforcement action applied.
        policy_id: Identifier of the policy that triggered this action.
        enforced_by: Identifier of the agent (human or automated) that acted.
        reason: Human-readable reason for the enforcement action.
        timestamp: UTC timestamp when the action was executed.
        metadata: Arbitrary additional fields (appeal status, region, etc.).
    """

    action_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    entity_id: str = Field(..., min_length=1)
    action_type: ActionType
    policy_id: str = Field(..., min_length=1, description="Policy that triggered this action")
    enforced_by: str = Field(..., min_length=1, description="Human or automated agent ID")
    reason: str = Field(..., min_length=1, max_length=5_000)
    timestamp: datetime = Field(..., description="UTC timestamp of the action")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_id": "user-bad-actor",
                    "action_type": "ban",
                    "policy_id": "policy-tos-v2",
                    "enforced_by": "auto-enforcer-v1",
                    "reason": "Repeated policy violations detected by classifier.",
                    "timestamp": "2026-03-22T08:00:00Z",
                    "metadata": {"appeal_window_days": 30, "region": "EU"},
                },
                {
                    "entity_id": "content-harmful-001",
                    "action_type": "content_removal",
                    "policy_id": "policy-csam-v1",
                    "enforced_by": "trust-safety-team",
                    "reason": "Content violates CSAM policy. Escalated to legal.",
                    "timestamp": "2026-03-22T07:45:00Z",
                    "metadata": {"legal_hold": True},
                },
            ]
        }
    }


class ModelOutput(BaseModel):
    """A recorded output from a generative model, used for safety auditing.

    Attributes:
        output_id: Unique identifier for this output record.
        model_id: Identifier of the generative model.
        prompt_hash: SHA-256 hash of the prompt (not stored in full for PII reasons).
        output_text: The raw text output from the model.
        safety_labels: Dict mapping safety categories to scores in [0.0, 1.0].
        latency_ms: Inference latency in milliseconds.
        timestamp: UTC timestamp when the output was generated.
        metadata: Arbitrary additional fields.
    """

    output_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_id: str = Field(..., min_length=1)
    prompt_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 hex digest")
    output_text: str = Field(..., min_length=1)
    safety_labels: dict[str, float] = Field(
        default_factory=dict,
        description="Safety category → score mapping, each in [0.0, 1.0]",
    )
    latency_ms: Annotated[int, Field(ge=0)] = 0
    timestamp: datetime = Field(..., description="UTC timestamp of generation")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("safety_labels")
    @classmethod
    def scores_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all safety scores are in [0.0, 1.0]."""
        for key, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"safety_labels[{key!r}]={score} is outside [0.0, 1.0]. "
                    "All safety scores must be probabilities."
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model_id": "claude-sonnet-4-6",
                    "prompt_hash": "a" * 64,
                    "output_text": "Here is a helpful and harmless answer.",
                    "safety_labels": {"toxicity": 0.02, "self_harm": 0.01, "pii": 0.00},
                    "latency_ms": 340,
                    "timestamp": "2026-03-22T11:00:00Z",
                    "metadata": {"temperature": 0.7, "max_tokens": 1024},
                },
                {
                    "model_id": "claude-haiku-4-5-20251001",
                    "prompt_hash": "b" * 64,
                    "output_text": "I cannot help with that request.",
                    "safety_labels": {"toxicity": 0.85, "prompt_injection": 0.72},
                    "latency_ms": 120,
                    "timestamp": "2026-03-22T11:05:00Z",
                    "metadata": {"temperature": 0.0, "max_tokens": 512},
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

SignalPayload = ClassifierOutput | UserReport | EnforcementLog | ModelOutput


class SignalEnvelope(BaseModel):
    """Wrapper around a signal payload carrying ingestion metadata.

    The envelope is the unit that flows through the ingestion pipeline.
    Invalid envelopes are written to raw.dead_letters with structured context.

    Attributes:
        envelope_id: Unique identifier for this envelope.
        signal_type: Discriminator field determining which payload model applies.
        payload: The typed signal payload.
        source: Originating system or service that emitted this signal.
        ingested_at: UTC timestamp when the envelope was created by the loader.
        loaded_at: UTC timestamp when the record landed in Snowflake (set by loader).
    """

    envelope_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    signal_type: SignalType
    payload: SignalPayload
    source: str = Field(..., min_length=1, description="Originating system identifier")
    ingested_at: datetime = Field(..., description="UTC timestamp of envelope creation")
    loaded_at: datetime | None = Field(None, description="UTC timestamp of Snowflake load")

    @model_validator(mode="after")
    def check_payload_type_matches_signal_type(self) -> SignalEnvelope:
        """Validate that payload model matches declared signal_type."""
        expected: dict[SignalType, type[SignalPayload]] = {
            SignalType.CLASSIFIER: ClassifierOutput,
            SignalType.REPORT: UserReport,
            SignalType.ENFORCEMENT: EnforcementLog,
            SignalType.MODEL_OUTPUT: ModelOutput,
        }
        expected_cls = expected[self.signal_type]
        if not isinstance(self.payload, expected_cls):
            raise ValueError(
                f"signal_type={self.signal_type!r} requires "
                f"{expected_cls.__name__} payload, got {type(self.payload).__name__}"
            )
        return self


class DeadLetter(BaseModel):
    """A failed ingestion record written to raw.dead_letters.

    Attributes:
        dead_letter_id: Unique identifier for this dead-letter record.
        raw_payload: The original payload that failed validation, as a dict.
        error_type: Class name of the exception that was raised.
        error_message: Stringified exception message.
        error_details: Structured field-level errors from Pydantic ValidationError.
        source: Originating system identifier.
        failed_at: UTC timestamp when validation failed.
    """

    dead_letter_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    raw_payload: dict[str, Any]
    error_type: str
    error_message: str
    error_details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured field-level errors extracted from ValidationError",
    )
    source: str
    failed_at: datetime


# Discriminated union helper used by loaders
SignalTypeAnnotation = Literal["classifier", "report", "enforcement", "model_output"]
