# Chronicle

Research-and-education prototype (hackathon Track 1) that reconstructs hospital Admissions from the **MIMIC-IV Clinical Database Demo v2.2** as timelines and answers natural-language questions with **Grounded Answers** only.

> Research and educational prototype only. Not for clinical use. Do not use for diagnosis, treatment, triage, or patient-specific recommendations.

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI + DuckDB (read-only over `*.csv.gz`) |
| UI | React + Vite + **shadcn/ui (Base UI, nova preset)** + TanStack Query/Router |
| LLM | DeepSeek V4-Flash via OpenCode Zen (`deepseek-v4-flash-free`) — tool/function calling |
| Run | `docker compose up` or local Makefile targets |

Patient rows **never** leave the machine. Only schema, Query Template descriptions, and the user question may egress (see [docs/adr/0001-schema-only-llm-egress.md](docs/adr/0001-schema-only-llm-egress.md)).

## One-command local run

```bash
cp .env.example .env   # set OPENCODE_API_KEY
make up                # fetches demo data if needed, then docker compose up --build
```

- UI: http://localhost:5173  
- API: http://localhost:8000/health  

### Local dev (without Docker)

```bash
make fetch-data
make install
make dev-api    # terminal 1 — :8000
make dev-web    # terminal 2 — :5173 (proxies API)
```

## Data

Frozen public PhysioNet **MIMIC-IV Clinical Database Demo v2.2** (ODbL). Fetched by `scripts/fetch-data.sh` into `data/mimic-iv-demo-2.2/` (gitignored). Source CSVs are opened **read-only** and never mutated.

Citation: Johnson, A., et al. MIMIC-IV Clinical Database Demo (version 2.2). PhysioNet. https://doi.org/10.13026/dp8b-2b12

## QA answer taxonomy

| Kind | Meaning |
|---|---|
| Grounded Answer | Rows retrieved; each fact has Provenance |
| No-Data Answer | Valid template, zero rows + per-Patient table coverage (e.g. eMAR 65/100) |
| Abstention | No template fits, or clinical-advice / out-of-scope request |

Bare unqualified “no” is never emitted. If the LLM API is unreachable, the **keyword baseline** runs and is labeled `keyword_fallback` in the UI.

## Tests & evaluation

```bash
make test           # HTTP + interpreter seam tests against real demo CSVs
make eval-offline   # Gold Set: oracle + keyword baseline → docs/eval/report.md
make eval           # also scores the live LLM interpreter
```

Gold Set: ~100 questions (fact, temporal, aggregate, unanswerable). Metrics: structured-fact accuracy, temporal-order accuracy, Provenance coverage, Abstention accuracy.

## Manual demo checklist

1. Open the UI — safety notice visible on every screen.  
2. Browse all 100 Patients; note eMAR coverage badges.  
3. Open a Patient → Admissions as chapters → expand timeline.  
4. Confirm ICU Stay intervals, collapsible ICU observation bands, Billing Context panel (untimed).  
5. Filter by event type / time window; reject invalid windows.  
6. Ask grounded questions (“How many transfers?”); inspect template, SQL, Provenance.  
7. Ask a Patient **without** eMAR about medications → No-Data + coverage.  
8. Ask clinical advice → Abstention.  
9. Stop the LLM / unset key → keyword fallback labeled in QA panel.  

## Configuration

| Env | Default | Purpose |
|---|---|---|
| `OPENCODE_API_KEY` | — | Zen API key |
| `LLM_BASE_URL` | `https://opencode.ai/zen/v1` | OpenAI-compatible base URL |
| `LLM_MODEL` | `deepseek-v4-flash-free` | Model ID (config-driven) |
| `INTERPRETER` | `llm` | `llm` \| `keyword` \| `fake` |
| `DATA_DIR` | `data/mimic-iv-demo-2.2` | Path to demo root |

## Repo layout

```
backend/     FastAPI, DuckDB, templates, interpreters, eval
frontend/    Vite + shadcn (Base UI / nova) + TanStack
data/        gitignored MIMIC demo
docs/        ADR, dataset/LLM facts, eval report
```

Domain vocabulary: [CONTEXT.md](CONTEXT.md).
