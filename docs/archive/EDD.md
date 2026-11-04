# Engineering Design Document (EDD): Local Telemetry & RAG Pipeline

## 1. System Overview & Objectives

- **Core Purpose:** Build a high-throughput, multi-tenant error logging and telemetry ingestion engine with a localized semantic search (RAG) layer.
- **Guiding Invariant:** _Strict separation of concerns._ Ingestion and telemetry metrics must remain 100% deterministic, fast, and isolated from probabilistic AI components.
- **Non-Goals (What we are NOT building):**
- We will **not** vectorize individual raw log lines.
- We will **not** use LLMs for filtering, parsing, or critical data transformation.

---

## 2. Component Boundaries & Contracts

### A. Ingestion Gateway (FastAPI)

- **Responsibility:** Validate incoming HTTP payloads, enforce rate limits, and push payloads to the async bus without blocking.
- **Invariants:**
- Must reject requests missing the `X-Tenant-ID` header with a `400 Bad Request`.
- Must respond with `202 Accepted` immediately after pushing to Redis. It must never wait for database writes or vector generation inline.

### B. Async Processing Worker Pool

- **Responsibility:** Consume streams, normalize errors, and write to storage.
- **Deterministic Rules (Signature Normalization):**
- Raw stack traces must pass through a normalization function (e.g., stripping memory addresses, dynamic line numbers, and absolute file paths) to generate a stable, deterministic **Signature Hash**.
- Duplicate errors within a sliding time window must increment a counter rather than create duplicate database rows.

### C. Storage Tiering Strategy

- **Hot Tier (PostgreSQL + Partitions):**
- Partitioned by `tenant_id` and timestamp.
- Retains structured aggregates, issue counts, and metadata for **30 days** for real-time dashboard querying.

- **Cold Tier (S3 / MinIO via Compressed JSONL Archive):**
- Raw log streams flushed asynchronously.
- Immutable historical record.

- **Vector Tier (PostgreSQL + `pgvector`):**
- Stores **Daily Narrative Summaries only** (not raw logs).
- Maintained via background rollups to support long-term semantic queries.

---

## 3. The Deterministic-to-AI Pipeline (Step 14 Specification)

This is the core contract governing how raw data becomes a vector. It ensures zero LLM non-determinism leaks into the telemetry core.

- **Trigger:** Daily cron worker running at 00:00 UTC.
- **Phase 1: Deterministic Aggregation (Code-Driven)**
- Query previous day's error aggregates and counts from PostgreSQL/S3 for a given tenant.
- Group strictly by `signature_hash`.
- Output: A structured JSON payload of metrics (e.g., `{"tenant": "X", "date": "2026-10-14", "top_errors": [{"sig": "...", "count": 142}]}`). _No LLM is involved here._

- **Phase 2: Probabilistic Narration (SLM-Driven)**
- Pass the _structured JSON metrics_ (never raw log lines) to the local Gemma SLM.
- **System Prompt Constraint:** _"You are a technical report writer. Translate these structured JSON telemetry metrics into a concise 2-sentence executive summary. Do not invent errors or metrics not present in the JSON."_

- **Phase 3: Embedding & Storage**
- Pass the generated summary string through `embeddinggemma-300m` with the required prefix format (`task: summary | text: ...`).
- Store the resulting 768-dim vector in `tenant_vector_summaries` alongside metadata (`tenant_id`, `log_date`, `granularity='daily'`).

---

## 4. Failure Modes & Mitigations

| Failure Scenario                 | System Impact                         | Mitigation Strategy                                                                                                                                         |
| -------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Redis Queue Spike / Crash**    | Ingestion blocked                     | Redis persistence (AOF/RDB) enabled; FastAPI drops back to HTTP 429/503 if stream buffer hits max memory.                                                   |
| **Ollama / Local LLM Down**      | Daily vector summary generation fails | The vector pipeline runs async in the background. It retries independently without affecting the core hot-path ingestion or React dashboard.                |
| **Non-Deterministic LLM Output** | Unpredictable summary phrasing        | Mitigated because the underlying metrics are pre-calculated deterministically in code; the LLM only writes human-readable wrapper text for vector matching. |
