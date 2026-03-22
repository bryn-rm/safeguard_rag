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

import subprocess

import typer

app = typer.Typer(
    name="safeguards-rag",
    help="Adaptive RAG agent for trust & safety operations.",
    add_completion=False,
)


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
    source: str = typer.Option("cli", "--source", help="Source identifier for ingested records."),
) -> None:
    """Ingest signals into Snowflake.

    With --synthetic, generates fake records using the Pydantic models
    and loads them through the normal validation + loader pipeline.

    Args:
        synthetic: Whether to generate synthetic data.
        count: Number of records to generate (synthetic mode only).
        source: Source identifier tag for the envelopes.
    """
    if synthetic:
        typer.echo(f"Generating {count} synthetic records (source={source!r})...")
        typer.echo("Synthetic data generation not yet implemented.")
    else:
        typer.echo("Live ingestion not yet implemented.")
    raise typer.Exit(code=1)


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
