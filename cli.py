"""CLI entry point for safeguards-rag.

Commands:
  query   Run the RAG pipeline on a natural-language query.
  ingest  Load synthetic or live signals into Snowflake.
  lint    Run ruff and mypy over the source tree.

Usage:
  python cli.py query "What is the false positive rate of toxicity-v3 this week?"
  python cli.py ingest --synthetic --count 1000
  python cli.py lint
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(
    name="safeguards-rag",
    help="Adaptive RAG agent for trust & safety operations.",
    add_completion=False,
)

SIGNALS_PATH = Path("data/signals.jsonl")


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural-language query to run through the pipeline."),
    config: str = typer.Option("configs/default.yaml", help="Path to pipeline config YAML."),
) -> None:
    """Run the RAG pipeline on a natural-language query.

    Args:
        question: The query to answer.
        config: Path to the pipeline configuration YAML file.
    """
    typer.echo(f"Query: {question}")
    typer.echo(f"Config: {config}")
    typer.echo("Pipeline not yet implemented.")
    raise typer.Exit(code=1)


@app.command()
def ingest(
    synthetic: bool = typer.Option(False, "--synthetic", help="Generate and load synthetic data."),
    count: int = typer.Option(100, "--count", help="Number of synthetic records to generate."),
    source: str = typer.Option("cli-synthetic", "--source", help="Source identifier for records."),
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
    out: str = typer.Option(str(SIGNALS_PATH), "--out", help="Output JSONL path for valid envelopes."),
) -> None:
    """Ingest signals into the pipeline.

    With --synthetic, generates a realistic mixed batch using SyntheticDataGenerator,
    runs every record through the appropriate loader, prints a summary table of
    counts by signal type and pass/fail, and writes valid envelopes to --out.

    Args:
        synthetic: Generate and use synthetic data instead of live sources.
        count: Number of records to generate (synthetic mode only).
        source: Source identifier stamped on every envelope.
        seed: Random seed for reproducible synthetic data.
        out: File path for the output JSONL of valid envelopes.
    """
    if not synthetic:
        typer.echo("Live ingestion not yet implemented. Use --synthetic to test.")
        raise typer.Exit(code=1)

    asyncio.run(_run_synthetic_ingest(count=count, source=source, seed=seed, out=Path(out)))


async def _run_synthetic_ingest(
    count: int,
    source: str,
    seed: int,
    out: Path,
) -> None:
    """Async implementation of the synthetic ingest command.

    Args:
        count: Total number of signals to generate.
        source: Source identifier for envelopes.
        seed: Random seed.
        out: Output JSONL path.
    """
    from src.ingestion.dead_letter import get_dead_letter_stats
    from src.ingestion.loaders.classifier import load_batch as load_classifier_batch
    from src.ingestion.loaders.enforcement import load_batch as load_enforcement_batch
    from src.ingestion.loaders.model_outputs import load_batch as load_model_batch
    from src.ingestion.loaders.reports import load_batch as load_report_batch
    from src.ingestion.synthetic import SyntheticDataGenerator

    typer.echo(f"Generating {count} synthetic signals (seed={seed}, source={source!r})...")
    gen = SyntheticDataGenerator(seed=seed)
    mixed = gen.generate_mixed_batch(count=count, source=source)

    # Bucket envelopes by signal type for per-loader processing
    from collections import defaultdict

    from src.ingestion.schemas import SignalType

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for env in mixed:
        buckets[env.signal_type].append(env.payload.model_dump(mode="json"))

    # Run each loader batch
    loader_map = {
        SignalType.CLASSIFIER: (load_classifier_batch, source),
        SignalType.REPORT: (load_report_batch, source),
        SignalType.ENFORCEMENT: (load_enforcement_batch, source),
        SignalType.MODEL_OUTPUT: (load_model_batch, source),
    }

    all_valid = []
    type_counts: Counter[str] = Counter()
    fail_counts: Counter[str] = Counter()

    for sig_type, (loader, src) in loader_map.items():
        recs = buckets.get(sig_type, [])
        if not recs:
            continue
        valid, failures = await loader(recs, src)
        all_valid.extend(valid)
        type_counts[sig_type] += len(valid)
        fail_counts[sig_type] += failures

    # Write valid envelopes to JSONL
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for env in all_valid:
            fh.write(env.model_dump_json() + "\n")

    # Summary table
    total_valid = sum(type_counts.values())
    total_fail = sum(fail_counts.values())

    typer.echo("")
    typer.echo("─" * 52)
    typer.echo(f"{'Signal type':<22} {'Valid':>8} {'Failed':>8} {'Total':>8}")
    typer.echo("─" * 52)
    for sig_type in [SignalType.CLASSIFIER, SignalType.REPORT,
                     SignalType.ENFORCEMENT, SignalType.MODEL_OUTPUT]:
        v = type_counts.get(sig_type, 0)
        f = fail_counts.get(sig_type, 0)
        typer.echo(f"{sig_type:<22} {v:>8} {f:>8} {v + f:>8}")
    typer.echo("─" * 52)
    typer.echo(f"{'TOTAL':<22} {total_valid:>8} {total_fail:>8} {total_valid + total_fail:>8}")
    typer.echo("─" * 52)

    typer.echo(f"\nValid envelopes written to: {out}")

    dl_stats = get_dead_letter_stats()
    if dl_stats:
        typer.echo(f"Dead-letter breakdown: {json.dumps(dl_stats, indent=2)}")
    else:
        typer.echo("No dead letters recorded.")


@app.command()
def lint() -> None:
    """Run ruff check and mypy over the source tree.

    Exits with code 0 only if both tools pass cleanly.
    """
    typer.echo("Running ruff check src/ ...")
    ruff_result = subprocess.run(
        ["ruff", "check", "src/"],
        capture_output=False,
    )

    typer.echo("\nRunning mypy src/ ...")
    mypy_result = subprocess.run(
        ["mypy", "src/"],
        capture_output=False,
    )

    if ruff_result.returncode != 0 or mypy_result.returncode != 0:
        typer.echo("\nLint/type-check failed.", err=True)
        raise typer.Exit(code=1)

    typer.echo("\nAll checks passed.")


if __name__ == "__main__":
    app()
