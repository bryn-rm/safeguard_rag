# safeguards-rag

An adaptive RAG agent for trust & safety operations. Ingests safety signals (classifier outputs, user reports, enforcement logs, model outputs), routes queries to the best retrieval strategy (SQL, vector search, keyword match), synthesises grounded answers, and self-evaluates confidence — retrying with an alternative strategy when the first pass falls short.

Built to demonstrate the full data engineering stack for trust & safety: ETL pipelines, Snowflake analytics, dbt transformations, data quality frameworks, dashboarding, and LLM-powered analytical tooling with LangSmith observability.

## Architecture

```
Signal sources (classifiers, reports, enforcement, model outputs)
  → Ingestion (Pydantic validation → Snowflake raw tables)
  → dbt (staging → intermediate → star schema marts)
  → LangGraph pipeline:
      router → retrieval (SQL | vector | keyword) → synthesis → confidence scorer
                ↑                                                      |
                └──────── retry with alternative strategy ←────────────┘
  → Streamlit dashboard + LangSmith traces
```

### LangGraph pipeline nodes

| Node | Model | Role |
|---|---|---|
| `router` | Claude Haiku | Classifies signal type, selects retrieval strategy |
| `retrieval_sql` | — | Renders Jinja2 SQL template, queries Snowflake |
| `retrieval_vector` | text-embedding-3-small | pgvector cosine search + MMR reranking |
| `retrieval_keyword` | — | PostgreSQL full-text search (tsvector/tsquery) |
| `synthesiser` | Claude Sonnet | Generates grounded answer with citations |
| `scorer` | Claude Sonnet | Self-evaluates faithfulness, returns confidence ∈ [0,1] |
| `retry` | — | Increments counter, clears stale state, loops back to router |

Low-confidence runs (score < 0.5) or runs with retries are auto-curated to the `safeguards-rag-eval` LangSmith dataset for regression testing.

### Snowflake star schema

```
fct_signals          — incremental fact table (high-watermark: _loaded_at)
dim_entities         — users and content items
dim_models           — classifier and generative models
dim_actions          — enforcement actions (FK → fct_signals)
```

## Tech stack

- **Agent orchestration**: LangGraph
- **LLMs**: Claude Haiku (routing), Claude Sonnet (synthesis + scoring)
- **Embeddings**: OpenAI text-embedding-3-small
- **Warehouse**: Snowflake
- **Vector store**: pgvector (PostgreSQL)
- **Transformation**: dbt
- **Orchestration**: Airflow
- **Validation**: Pydantic v2 (ingestion), Great Expectations (warehouse)
- **Observability**: LangSmith
- **Dashboard**: Streamlit
- **CLI**: Typer

## Project layout

```
src/pipeline/          # LangGraph agent: graph, state, nodes, retry controller
src/pipeline/nodes/    # One file per node
src/ingestion/         # Pydantic signal models, per-type loaders, dead-letter handler
src/retrieval/         # Jinja2 SQL templates, embedding client, pgvector client
src/quality/           # Great Expectations suites, freshness checks, alerting
src/dashboard/         # Streamlit app and chart components
dbt/                   # dbt project: staging → intermediate → marts
airflow/dags/          # Ingestion and transformation DAGs
configs/               # default.yaml, retrieval_templates.yaml
tests/                 # unit/, integration/, dbt/
cli.py                 # Typer CLI
```

## Quickstart

### 1. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set environment variables

```bash
export SNOWFLAKE_ACCOUNT=...
export SNOWFLAKE_USER=...
export SNOWFLAKE_PASSWORD=...
export SNOWFLAKE_DATABASE=safeguards_rag
export SNOWFLAKE_SCHEMA=marts
export SNOWFLAKE_WAREHOUSE=compute_wh
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export LANGSMITH_API_KEY=...
export LANGSMITH_PROJECT=safeguards-rag
export PGVECTOR_URL=postgresql://user:pass@host:5432/vectors
```

### 3. Run the pipeline

```bash
python cli.py query "What is the false positive rate of the toxicity classifier this week?"
```

### 4. Ingest synthetic test data

```bash
python cli.py ingest --synthetic --count 1000
```

### 5. Run dbt

```bash
cd dbt && dbt run && dbt test
```

### 6. Launch the dashboard

```bash
streamlit run src/dashboard/app.py
```

## Development

```bash
# Lint + type-check
ruff check src/ && ruff format --check src/ && mypy src/

# Or via CLI
python cli.py lint

# Run unit tests
pytest tests/unit/ -v

# Run all tests (requires Snowflake credentials for integration tests)
pytest tests/ -v
```

## Configuration

`configs/default.yaml` controls pipeline behaviour:

| Key | Default | Description |
|---|---|---|
| `pipeline.confidence_threshold` | `0.5` | Minimum score to accept an answer |
| `pipeline.max_retries` | `2` | Maximum retrieval retries per query |
| `retrieval.vector_top_k` | `10` | Candidates before MMR reranking |
| `retrieval.vector_final_k` | `5` | Documents after MMR reranking |
| `freshness.freshness_window_minutes.classifier` | `15` | Stale-data alert window (minutes) |
| `freshness.freshness_window_minutes.report` | `60` | Stale-data alert window (minutes) |

SQL retrieval templates are declared in `configs/retrieval_templates.yaml`. Each entry names a Jinja2 `.sql` file in `src/retrieval/templates/` and lists required parameters with types. Parameters are type-checked at runtime — register new templates there or the router will 404.

## Signal types

| Type | Pydantic model | Raw table |
|---|---|---|
| Classifier output | `ClassifierOutput` | `raw.classifier_outputs` |
| User report | `UserReport` | `raw.user_reports` |
| Enforcement log | `EnforcementLog` | `raw.enforcement_logs` |
| Model output | `ModelOutput` | `raw.model_outputs` |

Records that fail Pydantic validation are written to `raw.dead_letters` with structured error context (error type, message, source, timestamp). The dead-letter table is append-only — add a retention policy if storage becomes a concern.

## Data quality

- **Ingestion**: Pydantic v2 validates every record at the boundary. Invalid records go to dead letters.
- **Warehouse**: Great Expectations checkpoint runs after every dbt build. Suite covers column nulls, accepted values, row count anomalies, and data freshness.
- **Freshness alerts**: fire when no new signals arrive within the configured window (default: 15 min for classifiers, 60 min for reports).

## Notes

- The confidence scorer prompt is the most sensitive component — small wording changes shift score distributions. Always run the regression suite after editing `src/pipeline/nodes/scorer.py`.
- pgvector MMR reranking is applied in `src/retrieval/vector_store.py`. Do not add a second reranking step downstream.
- Snowflake incremental loads use `_loaded_at` as the high-watermark, not the signal's own `timestamp`, to handle late-arriving data correctly.
