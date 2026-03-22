"""Airflow DAG for dbt transformation and Great Expectations quality checks.

Runs after ingestion: executes dbt run + dbt test, then runs GE checkpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator

    _AIRFLOW_AVAILABLE = True
except ImportError:
    _AIRFLOW_AVAILABLE = False

DEFAULT_ARGS = {
    "owner": "safeguards-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def _run_ge_checkpoints() -> None:
    """Run Great Expectations checkpoints after dbt build."""
    raise NotImplementedError("GE checkpoints not yet implemented")


if _AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="safeguards_transform",
        default_args=DEFAULT_ARGS,
        description="Run dbt transformations and GE quality checks",
        schedule_interval="0 * * * *",  # hourly, after ingestion settles
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["safeguards", "dbt", "quality"],
    ) as transform_dag:
        t_dbt_run = BashOperator(
            task_id="dbt_run",
            bash_command="cd /opt/safeguards-rag/dbt && dbt run --profiles-dir /opt/safeguards-rag/dbt",
        )
        t_dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command="cd /opt/safeguards-rag/dbt && dbt test --profiles-dir /opt/safeguards-rag/dbt",
        )
        t_ge_checkpoints = PythonOperator(
            task_id="ge_checkpoints",
            python_callable=_run_ge_checkpoints,
        )

        t_dbt_run >> t_dbt_test >> t_ge_checkpoints
