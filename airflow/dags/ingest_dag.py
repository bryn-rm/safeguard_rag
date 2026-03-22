"""Airflow DAG for scheduled signal ingestion.

Runs each signal loader on a schedule and routes failures to dead letters.
"""

from __future__ import annotations

from datetime import datetime, timedelta

# Airflow imports are only available when running inside an Airflow environment.
# Guarded to allow the module to be imported for linting without Airflow installed.
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    _AIRFLOW_AVAILABLE = True
except ImportError:
    _AIRFLOW_AVAILABLE = False

DEFAULT_ARGS = {
    "owner": "safeguards-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _ingest_classifiers() -> None:
    """Placeholder task function for classifier ingestion."""
    raise NotImplementedError("Classifier ingestion task not yet implemented")


def _ingest_reports() -> None:
    """Placeholder task function for user report ingestion."""
    raise NotImplementedError("Report ingestion task not yet implemented")


def _ingest_enforcement() -> None:
    """Placeholder task function for enforcement log ingestion."""
    raise NotImplementedError("Enforcement ingestion task not yet implemented")


def _ingest_model_outputs() -> None:
    """Placeholder task function for model output ingestion."""
    raise NotImplementedError("Model output ingestion task not yet implemented")


if _AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="safeguards_ingest",
        default_args=DEFAULT_ARGS,
        description="Ingest safety signals from all sources into Snowflake raw tables",
        schedule_interval="*/15 * * * *",  # every 15 minutes
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["safeguards", "ingestion"],
    ) as ingest_dag:
        t_classifiers = PythonOperator(
            task_id="ingest_classifiers",
            python_callable=_ingest_classifiers,
        )
        t_reports = PythonOperator(
            task_id="ingest_reports",
            python_callable=_ingest_reports,
        )
        t_enforcement = PythonOperator(
            task_id="ingest_enforcement",
            python_callable=_ingest_enforcement,
        )
        t_model_outputs = PythonOperator(
            task_id="ingest_model_outputs",
            python_callable=_ingest_model_outputs,
        )

        # All loaders run in parallel
        [t_classifiers, t_reports, t_enforcement, t_model_outputs]
