# CLAUDE.md — safeguards-rag

## What this project is

An adaptive RAG agent for trust & safety operations, orchestrated with LangGraph and backed by Snowflake. It ingests safety signals (classifier outputs, user reports, enforcement logs, model outputs), routes queries to the best retrieval strategy (SQL, vector search, keyword match), synthesises grounded answers, and self-evaluates confidence — retrying with an alternative strategy if the first pass is insufficient.

The project demonstrates the full stack required for the Anthropic Data Engineer (Safeguards) role: ETL pipelines, Snowflake analytics, dbt transformations, data quality frameworks, dashboarding, and LLM-powered analytical tooling with LangSmith observability.

## Architecture at a glance

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

## Key directories

```
src/pipeline/          # LangGraph agent: graph, state, nodes
src/pipeline/nodes/    # router, retrieval_sql, retrieval_vector, retrieval_keyword, synthesiser, scorer
src/ingestion/         # Signal schemas (Pydantic), loaders per signal type, dead-letter handling
src/retrieval/         # SQL query templates (Jinja2), embedding logic, pgvector client
src/quality/           # Great Expectations suites, freshness checks, alerting
src/dashboard/         # Streamlit app and chart components
dbt/                   # dbt project: staging, intermediate, marts models + tests
airflow/dags/          # Ingestion and transformation DAGs
configs/               # Pipeline config, retrieval template registry
tests/                 # Unit + integration tests
```

## Tech stack

- **Agent orchestration**: LangGraph (StateGraph with conditional edges and retry loops)
- **Data orchestration**: Airflow or Dagster
- **Transformation**: dbt (SQL models, schema tests, data tests)
- **Warehouse**: Snowflake (star schema: fact_signals, dim_entities, dim_models, dim_actions)
- **Vector store**: pgvector (PostgreSQL)
- **LLMs**: Claude Haiku (router), Claude Sonnet (synthesis + confidence scorer)
- **Embeddings**: text-embedding-3-small or Cohere
- **Validation**: Pydantic (ingestion), Great Expectations (warehouse)
- **Observability**: LangSmith (traces, datasets, regression testing)
- **Dashboard**: Streamlit
- **CLI**: Typer

## Conventions

### Python
- Python 3.11+. Use `pyproject.toml` for all project config (no setup.py, no setup.cfg).
- Formatter: `ruff format`. Linter: `ruff check`. Type checker: `mypy --strict`.
- All public functions and classes have docstrings. Use Google-style docstrings.
- Pydantic v2 for all data models. Use `model_validator` for cross-field checks.
- Async by default for I/O-bound code (Snowflake queries, LLM calls, embedding requests). Use `asyncio.gather` for concurrent retrieval strategies during retries.

### LangGraph
- One file per node in `src/pipeline/nodes/`. Each node is a function `(state: PipelineState) -> dict` returning the state update.
- `PipelineState` is the single source of truth. Never pass data between nodes outside the state.
- Conditional edges use small pure functions that inspect state and return the next node name as a string. Keep routing logic out of the node functions.
- The retry loop is controlled by `src/pipeline/retry.py`. Max 2 retries. Strategy exclusion list lives in state.

### dbt
- Model naming: `stg_` prefix for staging, `int_` for intermediate, `fct_` / `dim_` for marts.
- Every model has a `.yml` schema file with column descriptions and tests.
- Use incremental materialisation for fact tables; table for dimensions.
- All timestamps are UTC. Use `timestamp_ntz` in Snowflake.

### SQL templates
- Retrieval SQL templates live in `src/retrieval/templates/` as Jinja2 `.sql` files.
- Templates are parameterised — never construct SQL by string concatenation.
- Template registry in `configs/retrieval_templates.yaml` maps template names to file paths and declares required parameters with types.

### Testing
- `tests/unit/` for pure logic (router classification, schema validation, retry controller).
- `tests/integration/` for end-to-end pipeline runs against a test Snowflake schema.
- `tests/dbt/` runs `dbt test` against seeded test data.
- CI smoke test: runs one full pipeline iteration (ingest synthetic data → query → retrieve → synthesise → score) and asserts confidence > 0.4.

### LangSmith
- Every node is traced. Metadata tags: `signal_type`, `retrieval_strategy`, `confidence_score`, `retry_count`.
- Auto-curation rules in `src/pipeline/graph.py`: save runs with confidence < 0.5 or retry_count > 0 to the `safeguards-rag-eval` dataset.
- Regression suite replays the curated dataset and asserts no confidence regression.

### Data quality
- Pydantic validation at ingestion. Invalid records go to `raw.dead_letters` with structured error context.
- Great Expectations checkpoint runs after every dbt build. Suite covers: column nulls, accepted values, row count anomalies, freshness.
- Freshness alerts fire if no new signals arrive within the configured window (default: 15 min for classifiers, 60 min for reports).

### Dashboard
- Streamlit app in `src/dashboard/app.py`. Components in `src/dashboard/components/`.
- Charts: signal volume (time series), strategy distribution (pie), confidence histogram, retry rate trend, data freshness gauges.
- No custom CSS. Use Streamlit native components and `st.metric` for KPIs.

### Git
- Branch naming: `feat/`, `fix/`, `chore/`, `docs/`.
- Commit messages: imperative mood, max 72 chars subject line. Body optional.
- PRs require passing CI (lint + type-check + unit tests + dbt test + smoke test).

## Common tasks

```bash
# Run the full pipeline on a query
python cli.py query "What is the false positive rate of the toxicity classifier this week?"

# Ingest synthetic test data
python cli.py ingest --synthetic --count 1000

# Run dbt transformations and tests
cd dbt && dbt run && dbt test

# Run the Streamlit dashboard
streamlit run src/dashboard/app.py

# Run all tests
pytest tests/ -v

# Lint and type-check
ruff check src/ && ruff format --check src/ && mypy src/
```

## Environment variables

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_DATABASE=safeguards_rag
SNOWFLAKE_SCHEMA=marts
SNOWFLAKE_WAREHOUSE=compute_wh
ANTHROPIC_API_KEY=
OPENAI_API_KEY=          # for embeddings (if using text-embedding-3-small)
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=safeguards-rag
PGVECTOR_URL=            # postgresql://user:pass@host:5432/vectors
```

## Things to watch out for

- The confidence scorer prompt is the most sensitive component. Small wording changes can shift the score distribution significantly. Always run the regression suite after editing `src/pipeline/nodes/scorer.py`.
- SQL template parameters are type-checked at runtime against the registry. If you add a new template, register it in `configs/retrieval_templates.yaml` or the router will 404.
- pgvector similarity search returns cosine distance by default. MMR reranking is applied in `src/retrieval/vector_store.py` — don't add a second reranking step downstream.
- Snowflake incremental loads use `_loaded_at` as the high-watermark column, not the signal's own `timestamp`. This avoids issues with late-arriving data.
- The dead-letter table (`raw.dead_letters`) is append-only and not cleaned up automatically. Add a retention policy if storage becomes a concern.
