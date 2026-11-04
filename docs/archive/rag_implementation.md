```
pip install asyncpg sentence-transformers httpx python-dotenv
```

**vector_worker.py**
```py
import asyncio
import os
from datetime import date, timedelta
from typing import List, Dict, Any
import asyncpg
import httpx
from sentence_transformers import SentenceTransformer

# Configuration from Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/vectordb")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b") # or gemma3:1b

# Initialize the 300M local embedding model on CPU/GPU
# embeddinggemma-300m supports MRL and instruction prefixes
embedder = SentenceTransformer("google/embeddinggemma-300m")

async def fetch_tenant_daily_metrics(conn: asyncpg.Connection, tenant_id: str, target_date: date) -> List[Dict[str, Any]]:
    """
    Step 1 & 2: Deterministic aggregation from PostgreSQL hot log aggregates.
    Groups strictly by deterministic signature hashes and sums counts.
    """
    query = """
        SELECT 
            signature_hash,
            service,
            log_level,
            SUM(event_count) as total_events,
            MIN(first_seen) as first_seen,
            MAX(last_seen) as last_seen,
            MAX(sample_message) as sample_message
        FROM hot_log_aggregates
        WHERE tenant_id = $1 
          AND created_at >= $2 
          AND created_at < $3
        GROUP BY signature_hash, service, log_level
        ORDER BY total_events DESC
        LIMIT 20;
    """
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    
    rows = await conn.fetch(query, tenant_id, start_dt, end_dt)
    return [dict(row) for row in rows]

async def generate_narrative_summary(metrics: List[Dict[str, Any]], target_date: date, tenant_id: str) -> str:
    """
    Step 3: Probabilistic Narration (SLM-Driven).
    Feeds pre-computed deterministic JSON stats to local Gemma via Ollama.
    """
    if not metrics:
        return f"For tenant {tenant_id} on {target_date.isoformat()}, system operations were stable with no logged errors or critical exceptions."

    prompt_payload = {
        "tenant_id": tenant_id,
        "date": target_date.isoformat(),
        "error_signatures": metrics
    }

    system_prompt = (
        "You are a technical site reliability engineering report writer. "
        "Translate the provided structured JSON telemetry metrics into a concise, 2-to-3 sentence executive narrative summary. "
        "Do not invent errors, metrics, or timestamps not present in the JSON."
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/v1/chat/completions",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": str(prompt_payload)}
                ],
                "temperature": 0.1 # Keep low for factual adherence
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

def generate_embedding(summary_text: str) -> List[float]:
    """
    Step 4: Embedding generation using embeddinggemma-300m.
    Applies the task instruction prefix recommended for embeddinggemma models.
    """
    formatted_input = f"task: summary | text: {summary_text}"
    embedding = embedder.encode(formatted_input, normalize_embeddings=True)
    return embedding.tolist() # 768-dimensional float vector

async def process_tenant_vector_pipeline(tenant_id: str, target_date: date):
    """
    Orchestrates the end-to-end background aggregation workflow for a single tenant.
    """
    print(f"[-] Starting vector rollup for tenant: {tenant_id} on {target_date}")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Deterministic Aggregation
        metrics = await fetch_tenant_daily_metrics(conn, tenant_id, target_date)
        total_errors = sum(m["total_events"] for m in metrics)

        # 2. Local SLM Narration
        summary_text = await generate_narrative_summary(metrics, target_date, tenant_id)
        print(f"[+] Generated summary: {summary_text[:100]}...")

        # 3. Vectorization
        vector = generate_embedding(summary_text)

        # 4. Save to pgvector Storage Layer
        insert_query = """
            INSERT INTO tenant_vector_summaries 
            (tenant_id, granularity, summary_text, start_date, end_date, total_error_count, embedding)
            VALUES ($1, 'daily', $2, $3, $3, $4, $5);
        """
        await conn.execute(
            insert_query,
            tenant_id,
            summary_text,
            target_date,
            total_errors,
            vector
        )
        print(f"[✓] Successfully stored daily vector summary for {tenant_id}")

    finally:
        await conn.close()

async def main():
    # Example execution for yesterday's logs across a target tenant
    target_date = date.today() - timedelta(days=1)
    sample_tenant_id = "tenant_acme_corp"
    
    await process_tenant_vector_pipeline(sample_tenant_id, target_date)

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
```

**search_api.py**
```sh
curl -X 'POST' \
  'http://localhost:8000/api/v1/rag/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: tenant_acme_corp' \
  d '{
  "query": "Why did database connection pools fail or timeout this week?",
  "limit": 2
}'
```

```py
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import asyncpg
import os
from typing import List

app = FastAPI(title="Telemetry RAG Search Gateway")

# Load embeddinggemma-300m model on startup
# (Shared globally or managed via app state in production)
embedder = SentenceTransformer("google/embeddinggemma-300m")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/vectordb")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1024, description="Natural language search query")
    limit: int = Field(5, ge=1, le=20, description="Max number of matching daily summaries to return")

class SearchResultResponse(BaseModel):
    summary_text: str
    start_date: str
    total_error_count: int
    similarity_score: float

@app.post("/api/v1/rag/search", response_model=List[SearchResultResponse])
async def tenant_semantic_search(
    payload: SearchRequest,
    x_tenant_id: str = Header(..., description="Tenant isolation ID header")
):
    """
    Performs semantic vector similarity search over a tenant's daily error summaries.
    """
    if not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="X-Tenant-ID header is required."
        )

    try:
        # 1. Format query using EmbeddingGemma instruction prefix for search retrieval
        formatted_query = f"task: search result | query: {payload.query}"
        
        # 2. Generate normalized 768-dim query vector
        query_vector = embedder.encode(formatted_query, normalize_embeddings=True).tolist()
        # Format list as a PostgreSQL vector literal string representation
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"

        # 3. Connect to PostgreSQL and query pgvector table
        # (In production, use a global connection pool dependency instead of creating per request)
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            sql = """
                SELECT 
                    summary_text,
                    start_date::text AS start_date,
                    total_error_count,
                    ROUND((1 - (embedding <=> $1::vector))::numeric, 4) AS similarity_score
                FROM tenant_vector_summaries
                WHERE tenant_id = $2
                ORDER BY embedding <=> $1::vector ASC
                LIMIT $3;
            """
            rows = await conn.fetch(sql, vector_str, x_tenant_id, payload.limit)
        finally:
            await conn.close()

        # 4. Map database rows to response schema
        results = [
            SearchResultResponse(
                summary_text=row["summary_text"],
                start_date=row["start_date"],
                total_error_count=row["total_error_count"],
                similarity_score=float(row["similarity_score"])
            )
            for row in rows
        ]

        return results

    except Exception as e:
        # Log exception in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )
```