## PostgreSQL Schema & Seed Data (schema.sql)
Run this in your local PostgreSQL database to set up your tables and insert your default rules:
```sql
-- 1. Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    log_message TEXT,
    level VARCHAR(50) DEFAULT 'INFO',
    trace_id VARCHAR(255),
    metadata JSONB, -- Stores endpoint, method, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Rule Definitions Table (Modify rules here without touching code!)
CREATE TABLE IF NOT EXISTS rule_definitions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    base_impact INT DEFAULT 5,
    base_likelihood INT DEFAULT 5,
    keywords TEXT[],
    scenario TEXT,
    observed_behavior TEXT,
    root_cause TEXT,
    business_impact TEXT,
    recommendations TEXT[]
);

-- 3. Pre-computed Issues Table (FastAPI reads directly from here)
CREATE TABLE IF NOT EXISTS issues (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(50),
    severity VARCHAR(50),
    risk_score NUMERIC(5, 2),
    endpoint VARCHAR(255),
    method VARCHAR(50),
    scenario TEXT,
    observed_behavior TEXT,
    root_cause TEXT,
    business_impact TEXT,
    recommendations TEXT[],
    evidence JSONB,
    timestamp TIMESTAMP WITH TIME ZONE
);

-- 4. Create Indexes for High-Performance Reads
CREATE INDEX IF NOT EXISTS idx_issues_risk_score ON issues (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_issues_category ON issues (category);
CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues (severity);

-- Seed initial rules into the database
INSERT INTO rule_definitions (title, category, base_impact, base_likelihood, keywords, scenario, observed_behavior, root_cause, business_impact, recommendations)
VALUES 
(
    'Stripe Gateway Connection Timeout',
    'FH', 8, 8,
    ARRAY['stripe', 'timeout'],
    'Timeout chains on payment gateway callbacks',
    'Checkouts hang for 15 seconds and crash with a gateway timeout error.',
    'Connect timeout is set to 30 seconds rather than failing fast.',
    'Direct revenue loss and abandoned carts during checkout spikes.',
    ARRAY['Reduce connect timeout to 3 seconds.', 'Add a fallback retry job on failure.']
),
(
    'Admin Dashboard Attack Route Probing',
    'SEC', 9, 9,
    ARRAY['unauthorized', 'admin', 'debug'],
    'Repeated unauthorized endpoint scans by bad actors',
    'Over 100 requests targeting private endpoints returning 401 unauthorized.',
    'Publicly accessible admin routing endpoints.',
    'Exposure risk and security compliance vulnerability.',
    ARRAY['Restrict internal routes at the gateway level.', 'Apply IP blacklist triggers in firewall.']
);
```

## The PL/pgSQL Dynamic Evaluation Function (function.sql)
Run this to create the stored procedure that evaluates rules against your logs and populates the issues table:
```sql
CREATE OR REPLACE FUNCTION refresh_detected_issues()
RETURNS VOID AS $$
DECLARE
    rule_record RECORD;
    group_record RECORD;
    computed_risk NUMERIC;
    computed_sev VARCHAR;
    issue_counter INT := 0;
    generated_id VARCHAR;
BEGIN
    -- Clear out previous cached issues
    TRUNCATE TABLE issues;

    -- Loop through every rule in the database
    FOR rule_record IN SELECT * FROM rule_definitions LOOP
        
        -- Group matching logs by endpoint and method found in metadata
        FOR group_record IN 
            SELECT 
                COALESCE(metadata->>'endpoint', '/api/v1/unknown') AS endpoint,
                COALESCE(metadata->>'method', 'POST') AS method,
                COUNT(*) AS matched_count,
                MAX(created_at) AS latest_ts,
                ARRAY_AGG(id::text) AS log_ids,
                ARRAY_AGG(trace_id) FILTER (WHERE trace_id IS NOT NULL AND trace_id != '') AS request_ids
            FROM logs
            WHERE (
                EXISTS (
                    SELECT 1 FROM unnest(rule_record.keywords) AS kw 
                    WHERE LOWER(log_message) LIKE '%' || LOWER(kw) || '%'
                )
                OR (
                    rule_record.category = 'OBS' 
                    AND 'trace' = ANY(rule_record.keywords) 
                    AND (trace_id IS NULL OR trace_id = '')
                )
            )
            GROUP BY COALESCE(metadata->>'endpoint', '/api/v1/unknown'), COALESCE(metadata->>'method', 'POST')
        LOOP
            -- Calculate risk score and severity
            computed_risk := ROUND((rule_record.base_impact * rule_record.base_likelihood * 0.1 + LEAST(group_record.matched_count * 0.05, 2.0))::numeric, 2);
            
            computed_sev := CASE 
                WHEN computed_risk >= 8.0 THEN 'CRI'
                WHEN computed_risk >= 5.0 THEN 'MED'
                ELSE 'LOW'
            END;

            issue_counter := issue_counter + 1;
            generated_id := computed_sev || '-' || rule_record.category || '-' || LPAD(issue_counter::text, 3, '0');

            -- Insert grouped result into issues table
            INSERT INTO issues (
                id, title, category, severity, risk_score, endpoint, method,
                scenario, observed_behavior, root_cause, business_impact,
                recommendations, evidence, timestamp
            ) VALUES (
                generated_id,
                rule_record.title,
                rule_record.category,
                computed_sev,
                computed_risk,
                group_record.endpoint,
                group_record.method,
                rule_record.scenario,
                rule_record.observed_behavior,
                rule_record.root_cause,
                rule_record.business_impact,
                rule_record.recommendations,
                json_build_object('log_ids', group_record.log_ids, 'request_ids', group_record.request_ids)::jsonb,
                group_record.latest_ts
            );
        END LOOP;
    END LOOP;
    
    -- Update table statistics for the query planner
    ANALYZE issues;
END;
$$ LANGUAGE plpgsql;
```

## FastAPI Backend Implementation (main.py)
```py
from fastapi import FastAPI, HTTPException
import asyncpg
from typing import List
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = "postgresql://postgres:password@localhost:5432/audit_db"

class IssueEvidence(BaseModel):
    log_ids: List[str] = []
    request_ids: List[str] = []

class IssueResponse(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    risk_score: float
    endpoint: str
    method: str
    scenario: str
    observed_behavior: str
    root_cause: str
    business_impact: str
    recommendations: List[str]
    evidence: IssueEvidence
    timestamp: str

@app.get("/api/audit/issues", response_model=List[IssueResponse])
async def detect_issues():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT * FROM issues ORDER BY risk_score DESC")
        await conn.close()
        
        result = []
        for row in rows:
            evidence_data = row["evidence"]
            result.append(
                IssueResponse(
                    id=row["id"],
                    title=row["title"],
                    category=row["category"],
                    severity=row["severity"],
                    risk_score=float(row["risk_score"]),
                    endpoint=row["endpoint"],
                    method=row["method"],
                    scenario=row["scenario"],
                    observed_behavior=row["observed_behavior"],
                    root_cause=row["root_cause"],
                    business_impact=row["business_impact"],
                    recommendations=row["recommendations"],
                    evidence=IssueEvidence(**evidence_data),
                    timestamp=row["timestamp"].isoformat() if row["timestamp"] else ""
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```