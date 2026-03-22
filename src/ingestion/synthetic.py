"""Synthetic signal generator for end-to-end pipeline testing.

Produces realistic fake signals for all four signal types without any external
dependencies (no Faker, no network calls). Uses only random and uuid from the
standard library.

Label distributions, score correlations, and type ratios are calibrated to
resemble a real trust & safety signal stream.
"""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from src.ingestion.schemas import (
    ActionType,
    ClassifierOutput,
    EnforcementLog,
    ModelOutput,
    ReportSeverity,
    ReportStatus,
    ReportType,
    SignalEnvelope,
    SignalType,
    UserReport,
)

# ---------------------------------------------------------------------------
# Label / category distributions
# ---------------------------------------------------------------------------

# Classifier: (label, weight, score_lo, score_hi)
_CLASSIFIER_LABELS: list[tuple[str, float, float, float]] = [
    ("clean", 0.70, 0.01, 0.35),
    ("toxicity", 0.15, 0.65, 0.99),
    ("pii", 0.10, 0.60, 0.95),
    ("prompt_injection", 0.05, 0.72, 0.99),
]

# Report: (type, weight)
_REPORT_TYPES: list[tuple[ReportType, float]] = [
    (ReportType.HARASSMENT, 0.35),
    (ReportType.SPAM, 0.30),
    (ReportType.HATE_SPEECH, 0.15),
    (ReportType.MISINFORMATION, 0.10),
    (ReportType.SELF_HARM, 0.05),
    (ReportType.CSAM, 0.03),
    (ReportType.OTHER, 0.02),
]

# Severity: (tier, weight) — skewed toward medium/low
_SEVERITY_WEIGHTS: list[tuple[ReportSeverity, float]] = [
    (ReportSeverity.LOW, 0.40),
    (ReportSeverity.MEDIUM, 0.40),
    (ReportSeverity.HIGH, 0.15),
    (ReportSeverity.CRITICAL, 0.05),
]

# Enforcement: (action_type, weight, reason_template)
_ENFORCEMENT_ACTIONS: list[tuple[ActionType, float, str]] = [
    (ActionType.WARN, 0.40, "First-time policy violation: {label}. Warning issued."),
    (
        ActionType.CONTENT_REMOVAL,
        0.30,
        "Content removed for violating {policy}: {label} detected with high confidence.",
    ),
    (ActionType.SUSPEND, 0.20, "Account suspended for repeated {label} violations (policy: {policy})."),
    (ActionType.BAN, 0.07, "Permanent ban: severe or repeat {label} violations (policy: {policy})."),
    (ActionType.SHADOWBAN, 0.02, "Shadowban applied: persistent low-severity {label} activity."),
    (ActionType.ESCALATE, 0.01, "Escalated to legal review: potential {label} requiring human assessment."),
]

# Model IDs used for model_output signals
_MODEL_IDS: list[str] = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-6",
]

# Classifier model IDs
_CLASSIFIER_MODEL_IDS: list[str] = [
    "toxicity-v3",
    "pii-detector-v1",
    "prompt-injection-v2",
    "spam-classifier-v4",
    "hate-speech-v2",
]

# Policy IDs
_POLICY_IDS: list[str] = [
    "policy-tos-v3",
    "policy-csam-v1",
    "policy-harassment-v2",
    "policy-spam-v2",
    "policy-hate-v1",
    "policy-pii-v1",
]

# Enforcer IDs
_ENFORCER_IDS: list[str] = [
    "auto-enforcer-v2",
    "trust-safety-team",
    "classifier-pipeline",
    "human-reviewer-pool",
]

# Sample output texts for model signals
_OUTPUT_TEXTS: list[str] = [
    "Here is a helpful and safe response to your question.",
    "I cannot assist with that request as it may cause harm.",
    "Based on the information provided, here is my analysis.",
    "I apologize, but I'm unable to provide that information.",
    "That's a great question! Let me explain step by step.",
    "I notice this request contains potentially harmful content.",
    "Here is a summary of the key points you asked about.",
    "I'll need more context before I can answer that safely.",
]

# Safety label categories for model output
_SAFETY_CATEGORIES: list[str] = [
    "toxicity",
    "self_harm",
    "pii",
    "prompt_injection",
    "hate_speech",
    "csam",
]


def _weighted_choice(options: list[tuple[Any, float]]) -> Any:
    """Pick one item from a weighted list.

    Args:
        options: List of (item, weight) pairs. Weights need not sum to 1.

    Returns:
        The chosen item.
    """
    items, weights = zip(*options, strict=True)
    return random.choices(list(items), weights=list(weights), k=1)[0]


def _random_timestamp(window_days: int = 7) -> datetime:
    """Return a random UTC timestamp within the last window_days.

    Args:
        window_days: How many days back to sample from.

    Returns:
        A timezone-aware UTC datetime.
    """
    offset_seconds = random.uniform(0, window_days * 86_400)
    return datetime.now(tz=UTC) - timedelta(seconds=offset_seconds)


def _fake_entity_id() -> str:
    """Return a fake content or user entity ID."""
    prefix = random.choice(["content", "user", "post", "comment"])
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _fake_user_id() -> str:
    """Return a fake user ID."""
    return f"user-{uuid.uuid4().hex[:10]}"


def _fake_prompt_hash() -> str:
    """Return a deterministic-looking SHA-256 hex digest."""
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


class SyntheticDataGenerator:
    """Generates realistic fake safety signals for all four signal types.

    All output is deterministic given the same random seed. No external
    dependencies are required.

    Args:
        seed: Optional random seed for reproducibility.
        window_days: Timestamp window — signals fall within the last N days.
        default_threshold: Default classifier decision threshold.
    """

    def __init__(
        self,
        seed: int | None = None,
        window_days: int = 7,
        default_threshold: float = 0.5,
    ) -> None:
        """Initialise the generator.

        Args:
            seed: Optional random seed for reproducibility.
            window_days: Signals are timestamped within the last N days.
            default_threshold: Classifier decision threshold applied to all outputs.
        """
        if seed is not None:
            random.seed(seed)
        self.window_days = window_days
        self.default_threshold = default_threshold

    # ------------------------------------------------------------------
    # Per-type generators
    # ------------------------------------------------------------------

    def _make_classifier_output(self, source: str) -> SignalEnvelope:
        """Generate one ClassifierOutput wrapped in a SignalEnvelope."""
        label, _, score_lo, score_hi = _weighted_choice(
            [(row, row[1]) for row in _CLASSIFIER_LABELS]
        )
        score = round(random.uniform(score_lo, score_hi), 4)
        is_positive = score >= self.default_threshold
        payload = ClassifierOutput(
            model_id=random.choice(_CLASSIFIER_MODEL_IDS),
            entity_id=_fake_entity_id(),
            label=label,
            score=score,
            threshold=self.default_threshold,
            is_positive=is_positive,
            timestamp=_random_timestamp(self.window_days),
            metadata={
                "model_version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
                "batch_id": uuid.uuid4().hex[:8],
            },
        )
        return SignalEnvelope(
            signal_type=SignalType.CLASSIFIER,
            payload=payload,
            source=source,
            ingested_at=datetime.now(tz=UTC),
        )

    def _make_user_report(self, source: str) -> SignalEnvelope:
        """Generate one UserReport wrapped in a SignalEnvelope."""
        report_type = _weighted_choice(_REPORT_TYPES)
        severity = _weighted_choice(_SEVERITY_WEIGHTS)

        descriptions: dict[ReportType, list[str]] = {
            ReportType.HARASSMENT: [
                "This user is sending threatening messages to me.",
                "I am being targeted with abusive content repeatedly.",
                "This account has been harassing multiple users in my community.",
            ],
            ReportType.SPAM: [
                "Repeatedly posting promotional links without consent.",
                "This account sends unsolicited commercial messages.",
                "Posting duplicate content across many channels.",
            ],
            ReportType.HATE_SPEECH: [
                "Content contains slurs and derogatory language targeting a group.",
                "This post promotes hatred against a religious minority.",
                "The user is making racist remarks in public threads.",
            ],
            ReportType.MISINFORMATION: [
                "This post contains demonstrably false health claims.",
                "Sharing manipulated media as if it were real news.",
                "Spreading conspiracy theories with no factual basis.",
            ],
            ReportType.SELF_HARM: [
                "User appears to be in crisis and may harm themselves.",
                "Post contains detailed self-harm methods.",
                "Requesting help on behalf of a friend who sent alarming messages.",
            ],
            ReportType.CSAM: [
                "Content depicts minors in inappropriate situations.",
                "Soliciting images from underage users.",
            ],
            ReportType.OTHER: [
                "Content violates community guidelines in a way not listed above.",
                "Unusual behaviour that does not fit other categories.",
            ],
        }
        description = random.choice(descriptions.get(report_type, ["Policy violation detected."]))

        payload = UserReport(
            reporter_id=_fake_user_id(),
            reported_entity_id=_fake_entity_id(),
            report_type=report_type,
            description=description,
            severity=severity,
            status=ReportStatus.PENDING,
            timestamp=_random_timestamp(self.window_days),
            metadata={
                "platform": random.choice(["web", "mobile", "api"]),
                "locale": random.choice(["en-US", "en-GB", "fr-FR", "de-DE", "es-ES"]),
            },
        )
        return SignalEnvelope(
            signal_type=SignalType.REPORT,
            payload=payload,
            source=source,
            ingested_at=datetime.now(tz=UTC),
        )

    def _make_enforcement_log(self, source: str) -> SignalEnvelope:
        """Generate one EnforcementLog wrapped in a SignalEnvelope."""
        action_type, _, reason_tpl = _weighted_choice(
            [(row, row[1]) for row in _ENFORCEMENT_ACTIONS]
        )
        policy_id = random.choice(_POLICY_IDS)
        label = random.choice(["toxicity", "spam", "hate_speech", "pii", "csam", "harassment"])
        reason = reason_tpl.format(label=label, policy=policy_id)

        payload = EnforcementLog(
            entity_id=_fake_entity_id(),
            action_type=action_type,
            policy_id=policy_id,
            enforced_by=random.choice(_ENFORCER_IDS),
            reason=reason,
            timestamp=_random_timestamp(self.window_days),
            metadata={
                "appeal_window_days": random.choice([0, 7, 14, 30]),
                "region": random.choice(["US", "EU", "APAC", "LATAM"]),
            },
        )
        return SignalEnvelope(
            signal_type=SignalType.ENFORCEMENT,
            payload=payload,
            source=source,
            ingested_at=datetime.now(tz=UTC),
        )

    def _make_model_output(self, source: str) -> SignalEnvelope:
        """Generate one ModelOutput wrapped in a SignalEnvelope."""
        model_id = random.choice(_MODEL_IDS)
        # Most outputs are safe; ~10% have elevated safety scores
        is_flagged = random.random() < 0.10
        safety_labels: dict[str, float] = {}
        for cat in random.sample(_SAFETY_CATEGORIES, k=random.randint(2, 4)):
            if is_flagged:
                safety_labels[cat] = round(random.uniform(0.55, 0.99), 4)
            else:
                safety_labels[cat] = round(random.uniform(0.00, 0.15), 4)

        payload = ModelOutput(
            model_id=model_id,
            prompt_hash=_fake_prompt_hash(),
            output_text=random.choice(_OUTPUT_TEXTS),
            safety_labels=safety_labels,
            latency_ms=random.randint(50, 500),
            timestamp=_random_timestamp(self.window_days),
            metadata={
                "temperature": round(random.uniform(0.0, 1.0), 2),
                "max_tokens": random.choice([256, 512, 1024, 2048]),
                "flagged": is_flagged,
            },
        )
        return SignalEnvelope(
            signal_type=SignalType.MODEL_OUTPUT,
            payload=payload,
            source=source,
            ingested_at=datetime.now(tz=UTC),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        signal_type: str,
        count: int,
        source: str = "synthetic-generator",
    ) -> list[SignalEnvelope]:
        """Generate a batch of signals of a single type.

        Args:
            signal_type: One of "classifier", "report", "enforcement",
                "model_output".
            count: Number of signals to generate.
            source: Source identifier written into each envelope.

        Returns:
            List of SignalEnvelope objects.

        Raises:
            ValueError: If signal_type is not recognised.
        """
        makers = {
            "classifier": self._make_classifier_output,
            "report": self._make_user_report,
            "enforcement": self._make_enforcement_log,
            "model_output": self._make_model_output,
        }
        if signal_type not in makers:
            raise ValueError(
                f"Unknown signal_type={signal_type!r}. "
                f"Valid values: {sorted(makers)}."
            )
        maker = makers[signal_type]
        return [maker(source) for _ in range(count)]

    def generate_mixed_batch(
        self,
        count: int,
        source: str = "synthetic-generator",
    ) -> list[SignalEnvelope]:
        """Generate a realistic mixed batch of all four signal types.

        Type proportions mirror a real signal stream:
          - classifier:  50%
          - report:      25%
          - enforcement: 15%
          - model_output: 10%

        Args:
            count: Total number of signals to generate.
            source: Source identifier written into each envelope.

        Returns:
            List of SignalEnvelope objects in randomised order.
        """
        type_weights: list[tuple[str, float]] = [
            ("classifier", 0.50),
            ("report", 0.25),
            ("enforcement", 0.15),
            ("model_output", 0.10),
        ]
        types, weights = zip(*type_weights, strict=True)
        chosen_types: list[str] = random.choices(list(types), weights=list(weights), k=count)

        makers = {
            "classifier": self._make_classifier_output,
            "report": self._make_user_report,
            "enforcement": self._make_enforcement_log,
            "model_output": self._make_model_output,
        }
        return [makers[t](source) for t in chosen_types]
