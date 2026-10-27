import type {
  Log,
  Stats,
  TrendPoint,
  Issue,
  AuditIssue,
  Alert,
  Report,
} from "./api";

// Helper for generating dynamic timestamps relative to now
const now = new Date();
const minutesAgo = (mins: number) =>
  new Date(now.getTime() - mins * 60 * 1000).toISOString();
const hoursAgo = (hours: number) =>
  new Date(now.getTime() - hours * 60 * 60 * 1000).toISOString();
const daysAgo = (days: number) =>
  new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString();

// In-memory dummy logs collection with interactive mutations
const initialLogs: Log[] = [
  // Trace 1: Checkout cascade failure (trc_92a18d)
  {
    id: "log_001",
    service: "gateway",
    environment: "production",
    level: "INFO",
    log_message: "HTTP POST /v1/checkout/process received from IP 192.168.1.105",
    trace_id: "trc_92a18d",
    metadata: {
      route: "/v1/checkout/process",
      method: "POST",
      client_ip: "192.168.1.105",
      user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    },
    created_at: minutesAgo(8),
  },
  {
    id: "log_002",
    service: "auth-service",
    environment: "production",
    level: "INFO",
    log_message: "Bearer JWT authenticated successfully for user_id usr_4920",
    trace_id: "trc_92a18d",
    metadata: {
      user_id: "usr_4920",
      tenant_id: "ten_live_9918",
      token_type: "Bearer",
      claims: ["read:checkout", "write:orders"],
    },
    created_at: minutesAgo(7.8),
  },
  {
    id: "log_003",
    service: "payment-api",
    environment: "production",
    level: "CRITICAL",
    log_message:
      "Database connection timeout on pool-size 50 while acquiring transaction lock",
    trace_id: "trc_92a18d",
    metadata: {
      db_pool_active: 50,
      db_pool_max: 50,
      query: "SELECT * FROM accounts WHERE id = $1 FOR UPDATE",
      wait_duration_ms: 5002,
      error_code: "POOL_TIMEOUT",
    },
    created_at: minutesAgo(7.2),
  },
  {
    id: "log_004",
    service: "gateway",
    environment: "production",
    level: "ERROR",
    log_message:
      "HTTP 504 Gateway Timeout downstream payment-api after 5000ms SLA cap",
    trace_id: "trc_92a18d",
    metadata: {
      status_code: 504,
      downstream_service: "payment-api",
      elapsed_ms: 5012,
    },
    created_at: minutesAgo(7.1),
  },

  // Trace 2: Auth brute-force attempt (trc_auth_8821)
  {
    id: "log_005",
    service: "auth-service",
    environment: "production",
    level: "WARNING",
    log_message:
      "Failed login attempt: invalid credentials provided for devops@company.internal",
    trace_id: "trc_auth_8821",
    metadata: {
      target_account: "devops@company.internal",
      attempt_count: 4,
      origin_country: "US",
      asn: "AS15169",
    },
    created_at: minutesAgo(14),
  },
  {
    id: "log_006",
    service: "auth-service",
    environment: "production",
    level: "ERROR",
    log_message:
      "Rate limit exceeded: 5 failed login attempts in 60s for IP 203.0.113.42",
    trace_id: "trc_auth_8821",
    metadata: {
      ip: "203.0.113.42",
      window_seconds: 60,
      limit: 5,
      action: "TEMPORARY_BLOCK_15M",
    },
    created_at: minutesAgo(13.8),
  },

  // Trace 3: Inventory race condition (trc_b3f71c)
  {
    id: "log_007",
    service: "gateway",
    environment: "production",
    level: "INFO",
    log_message: "POST /v1/orders/reserve dispatched to inventory-service",
    trace_id: "trc_b3f71c",
    metadata: {
      sku: "SKU-9921-ALPHA",
      quantity: 2,
      order_id: "ord_77189a",
    },
    created_at: minutesAgo(25),
  },
  {
    id: "log_008",
    service: "inventory-service",
    environment: "production",
    level: "ERROR",
    log_message:
      "Deadlock detected while waiting for lock in table inventory_items",
    trace_id: "trc_b3f71c",
    metadata: {
      relation: "inventory_items",
      blocked_pid: 24891,
      blocking_pid: 24884,
      query: "UPDATE inventory_items SET stock = stock - 2 WHERE sku = 'SKU-9921-ALPHA'",
    },
    created_at: minutesAgo(24.5),
  },

  // Trace 4: Billing engine invoice generation (trc_e0129a)
  {
    id: "log_009",
    service: "billing-engine",
    environment: "production",
    level: "INFO",
    log_message:
      "Subscription renewal processed successfully for tenant ten_acme_corp",
    trace_id: "trc_e0129a",
    metadata: {
      tenant_id: "ten_acme_corp",
      invoice_id: "inv_2026_09281",
      amount_usd: 1250.0,
      plan: "Enterprise Scale",
    },
    created_at: minutesAgo(35),
  },
  {
    id: "log_010",
    service: "notification-worker",
    environment: "production",
    level: "INFO",
    log_message: "Receipt email dispatch completed via AWS SES in 142ms",
    trace_id: "trc_e0129a",
    metadata: {
      provider: "AWS SES",
      recipient_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      template: "invoice_receipt_v2",
      latency_ms: 142,
    },
    created_at: minutesAgo(34.8),
  },

  // Trace 5: Webhook delivery timeout (trc_whk_019a)
  {
    id: "log_011",
    service: "notification-worker",
    environment: "production",
    level: "WARNING",
    log_message:
      "Outbound webhook delivery delayed: customer endpoint responded with HTTP 429",
    trace_id: "trc_whk_019a",
    metadata: {
      target_url: "https://api.partner.io/webhooks/sentry-events",
      retry_attempt: 2,
      next_retry_delay_sec: 30,
      response_code: 429,
    },
    created_at: minutesAgo(50),
  },

  // General service logs
  {
    id: "log_012",
    service: "auth-service",
    environment: "production",
    level: "INFO",
    log_message: "OAuth2 key rotation check: active RS256 key valid until 2027-01-01",
    trace_id: "trc_sys_001",
    metadata: {
      key_id: "kid_prod_2026_v1",
      algorithm: "RS256",
      status: "HEALTHY",
    },
    created_at: hoursAgo(1.2),
  },
  {
    id: "log_013",
    service: "gateway",
    environment: "production",
    level: "INFO",
    log_message: "TLS 1.3 handshake negotiated with cipher TLS_AES_256_GCM_SHA384",
    trace_id: "trc_gw_9981",
    metadata: {
      protocol: "TLSv1.3",
      cipher: "TLS_AES_256_GCM_SHA384",
      http_version: "HTTP/2",
    },
    created_at: hoursAgo(1.5),
  },
  {
    id: "log_014",
    service: "payment-api",
    environment: "production",
    level: "INFO",
    log_message: "Stripe payout settlement batch synced: 142 transactions processed",
    trace_id: "trc_pay_7721",
    metadata: {
      settled_count: 142,
      gross_amount_usd: 18450.0,
      fee_usd: 535.05,
    },
    created_at: hoursAgo(2),
  },
  {
    id: "log_015",
    service: "gateway",
    environment: "staging",
    level: "INFO",
    log_message: "Deployment canary traffic switched: 10% routed to staging-v1.4",
    trace_id: "trc_canary_01",
    metadata: {
      canary_version: "v1.4.0-rc3",
      traffic_split_percent: 10,
      canary_healthy: true,
    },
    created_at: hoursAgo(2.8),
  },
  {
    id: "log_016",
    service: "billing-engine",
    environment: "production",
    level: "WARNING",
    log_message: "Proration calculation discrepancy corrected for invoice inv_2026_09110",
    trace_id: "trc_bill_4401",
    metadata: {
      original_delta: -0.04,
      adjusted_total: 89.96,
      reason: "leap_year_rounding",
    },
    created_at: hoursAgo(3.2),
  },
  {
    id: "log_017",
    service: "inventory-service",
    environment: "production",
    level: "WARNING",
    log_message: "Inventory threshold alert: SKU-WIRELESS-EARBUDS below safety buffer (qty: 3)",
    trace_id: "trc_inv_1092",
    metadata: {
      sku: "SKU-WIRELESS-EARBUDS",
      remaining_units: 3,
      reorder_point: 25,
      supplier_notified: true,
    },
    created_at: hoursAgo(4),
  },
  {
    id: "log_018",
    service: "notification-worker",
    environment: "production",
    level: "INFO",
    log_message: "Push notification batch completed: 4,810 APNs tokens sent via HTTP/2",
    trace_id: "trc_push_0921",
    metadata: {
      platform: "Apple APNs",
      delivered: 4802,
      expired_tokens: 8,
      latency_p95_ms: 88,
    },
    created_at: hoursAgo(4.5),
  },
  {
    id: "log_019",
    service: "payment-api",
    environment: "staging",
    level: "INFO",
    log_message: "Mock 3DS challenge completed in sandbox environment",
    trace_id: "trc_sand_5501",
    metadata: {
      auth_result: "AUTHENTICATED",
      eci: "05",
      cavv: "AAABBIIFmQAAAAAAAABmEAAAAAA=",
    },
    created_at: hoursAgo(5),
  },
  {
    id: "log_020",
    service: "gateway",
    environment: "production",
    level: "INFO",
    log_message: "Redis sliding window rate limit metrics flushed to Prometheus",
    trace_id: "trc_sys_002",
    metadata: {
      active_rate_limit_keys: 841,
      peak_requests_per_sec: 1420,
      dropped_requests_window: 12,
    },
    created_at: hoursAgo(6),
  },
  {
    id: "log_021",
    service: "auth-service",
    environment: "production",
    level: "CRITICAL",
    log_message: "Security exception: Malformed JWT header algorithm 'none' rejected",
    trace_id: "trc_sec_9931",
    metadata: {
      ip: "198.51.100.17",
      attempted_algorithm: "none",
      header_dump: '{"alg":"none","typ":"JWT"}',
      threat_level: "HIGH",
    },
    created_at: hoursAgo(7),
  },
  {
    id: "log_022",
    service: "inventory-service",
    environment: "production",
    level: "INFO",
    log_message: "Warehouse sync job completed: 18,400 catalog units refreshed",
    trace_id: "trc_sync_004",
    metadata: {
      duration_seconds: 14.2,
      records_updated: 18400,
      checksum: "sha256_d89201f8",
    },
    created_at: hoursAgo(8),
  },
];

// Live in-memory copy that can be modified via create/delete during demo
let liveLogs: Log[] = [...initialLogs];

// Dummy stats derived from rich distribution
export const getDummyStats = async (): Promise<Stats> => {
  // Small simulated latency for natural UI transitions
  await new Promise((resolve) => setTimeout(resolve, 80));

  const total = liveLogs.length;
  const by_level: Record<string, number> = {};
  const by_service: Record<string, number> = {};
  const by_environment: Record<string, number> = {};

  liveLogs.forEach((l) => {
    by_level[l.level] = (by_level[l.level] || 0) + 1;
    by_service[l.service] = (by_service[l.service] || 0) + 1;
    by_environment[l.environment] = (by_environment[l.environment] || 0) + 1;
  });

  const errorCount = (by_level["ERROR"] || 0) + (by_level["CRITICAL"] || 0);
  const errorRate = total > 0 ? Number(((errorCount / total) * 100).toFixed(2)) : 0;

  return {
    total_count: 14892 + total, // Realistic scale combined with active logs
    by_level: {
      INFO: 13410 + (by_level["INFO"] || 0),
      WARNING: 982 + (by_level["WARNING"] || 0),
      ERROR: 420 + (by_level["ERROR"] || 0),
      CRITICAL: 80 + (by_level["CRITICAL"] || 0),
    },
    by_service: {
      gateway: 6240 + (by_service["gateway"] || 0),
      "auth-service": 3810 + (by_service["auth-service"] || 0),
      "payment-api": 2940 + (by_service["payment-api"] || 0),
      "billing-engine": 1120 + (by_service["billing-engine"] || 0),
      "notification-worker": 782 + (by_service["notification-worker"] || 0),
      "inventory-service": 540 + (by_service["inventory-service"] || 0),
    },
    by_environment: {
      production: 12640 + (by_environment["production"] || 0),
      staging: 2252 + (by_environment["staging"] || 0),
    },
    error_rate: errorRate || 3.36,
  };
};

// 24-hour dynamic hourly trend points
export const getDummyTrends = async (): Promise<TrendPoint[]> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  const trends: TrendPoint[] = [];
  const current = new Date();

  // Pattern of realistic traffic over 24 hours
  const baseCurves = [
    42, 35, 28, 22, 19, 25, 45, 85, 140, 210, 260, 295, 310, 285, 270, 290,
    320, 310, 280, 230, 180, 140, 95, 60,
  ];

  for (let i = 23; i >= 0; i--) {
    const d = new Date(current.getTime() - i * 60 * 60 * 1000);
    const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:00`;

    const hourIdx = (d.getHours() + 24) % 24;
    const baseTotal = baseCurves[hourIdx] + Math.floor(Math.random() * 20);
    const errorCount = Math.floor(baseTotal * 0.035) + (hourIdx === 16 ? 12 : 1);
    const warningCount = Math.floor(baseTotal * 0.07) + (hourIdx === 14 ? 8 : 2);
    const infoCount = baseTotal - errorCount - warningCount;

    trends.push({
      timestamp: dateStr,
      info_count: Math.max(1, infoCount),
      warning_count: Math.max(0, warningCount),
      error_count: Math.max(0, errorCount),
      total_count: baseTotal,
    });
  }

  return trends;
};

// Recurring issues for Dashboard
export const getDummyIssues = async (): Promise<Issue[]> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  return [
    {
      id: "iss_01",
      service: "payment-api",
      level: "CRITICAL",
      environment: "production",
      message: "Database connection timeout on pool-size 50 while acquiring transaction lock",
      count: 42,
      first_seen: daysAgo(2),
      last_seen: minutesAgo(7),
      status: "UNRESOLVED",
      assigned_to: "Angelo Arcillas",
    },
    {
      id: "iss_02",
      service: "auth-service",
      level: "ERROR",
      environment: "production",
      message: "Rate limit exceeded: 5 failed login attempts in 60s",
      count: 28,
      first_seen: daysAgo(1),
      last_seen: minutesAgo(14),
      status: "INVESTIGATING",
      assigned_to: "Security Team",
    },
    {
      id: "iss_03",
      service: "inventory-service",
      level: "ERROR",
      environment: "production",
      message: "Deadlock detected while waiting for lock in table inventory_items",
      count: 17,
      first_seen: daysAgo(3),
      last_seen: minutesAgo(24),
      status: "UNRESOLVED",
      assigned_to: "Database Admin",
    },
    {
      id: "iss_04",
      service: "gateway",
      level: "WARNING",
      environment: "production",
      message: "Downstream latency exceeded SLA threshold (p99 > 850ms)",
      count: 14,
      first_seen: daysAgo(4),
      last_seen: hoursAgo(1),
      status: "RESOLVED",
      assigned_to: "Infrastructure Team",
    },
    {
      id: "iss_05",
      service: "notification-worker",
      level: "WARNING",
      environment: "production",
      message: "Outbound webhook delivery delayed: customer endpoint returned 429",
      count: 9,
      first_seen: daysAgo(1),
      last_seen: minutesAgo(50),
      status: "INVESTIGATING",
      assigned_to: "Integration On-Call",
    },
  ];
};

// Comprehensive Reliability Audit Issues for /issues page
export const getDummyAuditIssues = async (filters?: {
  id?: string;
  severity?: string;
  category?: string;
  endpoint?: string;
}): Promise<AuditIssue[]> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  const allAuditIssues: AuditIssue[] = [
    {
      id: "CRI-DI-001",
      title: "Duplicate Payment Transaction Ingestion",
      category: "DI",
      severity: "CRI",
      risk_score: 9.42,
      endpoint: "/v1/checkout/process",
      method: "POST",
      scenario: "Multiple identical checkout requests processed in millisecond succession during network retransmits.",
      observed_behavior: "System processes duplicate payment authorizations without idempotency check, creating duplicate customer billing entries.",
      root_cause: "Missing Idempotency-Key validation header and lack of Redis distributed mutex lock on checkout transactions.",
      business_impact: "Double-billing of active customers, payment dispute chargeback penalties, and ledger reconciliation overhead.",
      recommendations: [
        "Enforce mandatory Idempotency-Key HTTP headers for all mutating payment API routes.",
        "Implement distributed Redis lock with a 10-second TTL keyed by client idempotency token.",
        "Add database unique constraint on (tenant_id, idempotency_key).",
      ],
      evidence: {
        log_ids: ["log_001", "log_003", "log_004"],
        request_ids: ["req_8819a", "req_8819b"],
      },
      timestamp: minutesAgo(7),
    },
    {
      id: "CRI-CON-001",
      title: "Database Transaction Deadlock on Inventory Table",
      category: "CON",
      severity: "CRI",
      risk_score: 8.85,
      endpoint: "/v1/orders/reserve",
      method: "POST",
      scenario: "High-volume flash sale causes concurrent workers contending for identical inventory item rows.",
      observed_behavior: "PostgreSQL transaction deadlocks detected; worker connection threads stall until connection pool timeout.",
      root_cause: "SELECT FOR UPDATE lock ordering inconsistent across order checkout and stock reservation actions.",
      business_impact: "Spikes in checkout latency from 120ms to 5000ms+, causing 14% customer cart abandonment.",
      recommendations: [
        "Standardize row-locking sequence alphabetically by product_sku across all database queries.",
        "Apply optimistic locking with version column verification instead of row-level exclusive locks.",
        "Introduce Redis token-bucket inventory reservation before hitting relational database.",
      ],
      evidence: {
        log_ids: ["log_007", "log_008"],
        request_ids: ["req_7124f", "req_7124g"],
      },
      timestamp: minutesAgo(24),
    },
    {
      id: "CRI-SEC-001",
      title: "Algorithm Confusion Vulnerability in Bearer Token Verifier",
      category: "SEC",
      severity: "CRI",
      risk_score: 9.8,
      endpoint: "/v1/auth/verify",
      method: "POST",
      scenario: "Attacker transmits tokens with header alg='none' or mismatched symmetric algorithm against RS256 verifier.",
      observed_behavior: "Signature validation bypass allowed when token header specified 'none' or mismatched HMAC secret.",
      root_cause: "JWT verification library allowed dynamic algorithm selection from token header without strict whitelist enforcement.",
      business_impact: "Potential unauthenticated tenant privilege escalation and critical data breach exposure.",
      recommendations: [
        "Explicitly specify algorithms=['RS256'] in PyJWT decode settings.",
        "Reject any tokens containing 'none' or unexpected algorithm headers at the API gateway layer.",
        "Rotate verification keys and invalidate legacy bearer sessions.",
      ],
      evidence: {
        log_ids: ["log_021"],
        request_ids: ["req_9931z"],
      },
      timestamp: hoursAgo(7),
    },
    {
      id: "MED-FH-001",
      title: "Connection Pool Exhaustion During Payment Gateway Latency",
      category: "FH",
      severity: "MED",
      risk_score: 6.75,
      endpoint: "/v1/payments/stripe/webhook",
      method: "POST",
      scenario: "Third-party payment provider experiences upstream latency, holding open database connections.",
      observed_behavior: "SQLAlchemy connection pool depleted (50/50 connections active); subsequent incoming HTTP requests fail with 503.",
      root_cause: "Synchronous external HTTP request executed inside active database transaction block.",
      business_impact: "Cascading outage of unrelated read endpoints due to database pool starvation.",
      recommendations: [
        "Separate third-party API calls from database transactions using asynchronous event queues.",
        "Configure strict 3-second HTTP timeout on all outbound payment webhook calls.",
        "Enable connection pool overflow and implement circuit breaker pattern.",
      ],
      evidence: {
        log_ids: ["log_003"],
        request_ids: ["req_4401c"],
      },
      timestamp: minutesAgo(8),
    },
    {
      id: "MED-DI-002",
      title: "Inconsistent Order Status Lifecycle State Transition",
      category: "DI",
      severity: "MED",
      risk_score: 5.9,
      endpoint: "/v1/orders/status",
      method: "PATCH",
      scenario: "Canceled orders transition directly to 'Shipped' when concurrent webhook events arrive out-of-order.",
      observed_behavior: "Order status transitioned from 'CANCELLED' to 'FULFILLED', triggering automated warehouse dispatch.",
      root_cause: "Missing state transition state-machine validation before committing status changes.",
      business_impact: "Incorrect physical product shipment for refunded customers, incurring lost inventory costs.",
      recommendations: [
        "Implement finite state machine (FSM) defining valid transition graphs.",
        "Add database trigger or check constraint forbidding transitions out of terminal states.",
      ],
      evidence: {
        log_ids: ["log_009"],
        request_ids: ["req_3182k"],
      },
      timestamp: minutesAgo(35),
    },
    {
      id: "LOW-OBS-001",
      title: "Uncorrelated Microservice Span Traces",
      category: "OBS",
      severity: "LOW",
      risk_score: 3.4,
      endpoint: "/v1/notifications/email",
      method: "POST",
      scenario: "Asynchronous Celery tasks execute without forwarding incoming HTTP trace headers.",
      observed_behavior: "Notification worker logs appear disconnected from parent checkout requests in trace explorer.",
      root_cause: "Task dispatch helper drops W3C traceparent and trace_id headers during queue serialization.",
      business_impact: "Increased Mean Time to Resolution (MTTR) during notification delivery diagnostic investigations.",
      recommendations: [
        "Inject trace_id and span_id into Celery message headers during task.delay() calls.",
        "Configure OpenTelemetry context propagation across Redis task queues.",
      ],
      evidence: {
        log_ids: ["log_010", "log_011"],
        request_ids: ["req_1044p"],
      },
      timestamp: minutesAgo(50),
    },
    {
      id: "LOW-OBS-002",
      title: "Missing Structured Error Metadata on Rate-Limit 429 Responses",
      category: "OBS",
      severity: "LOW",
      risk_score: 2.8,
      endpoint: "/v1/logs",
      method: "POST",
      scenario: "FastAPI rate-limiting middleware emits plain text 429 responses instead of RFC 7807 JSON.",
      observed_behavior: "Client log forwarders fail to parse rate-limit feedback and retry aggressively without exponential backoff.",
      root_cause: "Default Starlette exception handler bypassed application-level JSON response formatting.",
      business_impact: "Client SDKs unable to inspect Retry-After backoff intervals, exacerbating ingress traffic spikes.",
      recommendations: [
        "Implement RFC 7807 compliant Problem Details schema for all HTTP 429 and 503 error responses.",
        "Ensure Retry-After header is accompanied by retry_after_ms in the JSON response payload.",
      ],
      evidence: {
        log_ids: ["log_006"],
        request_ids: ["req_0921m"],
      },
      timestamp: minutesAgo(13),
    },
  ];

  // Apply filters if provided
  return allAuditIssues.filter((issue) => {
    if (filters?.id && !issue.id.toLowerCase().includes(filters.id.toLowerCase())) {
      return false;
    }
    if (filters?.severity && issue.severity !== filters.severity) {
      return false;
    }
    if (filters?.category && issue.category !== filters.category) {
      return false;
    }
    if (
      filters?.endpoint &&
      !issue.endpoint?.toLowerCase().includes(filters.endpoint.toLowerCase())
    ) {
      return false;
    }
    return true;
  });
};

// Generate valid minimal PDF blob for demo export
export const exportDummyAuditPdf = async (): Promise<Blob> => {
  await new Promise((resolve) => setTimeout(resolve, 400));

  const pdfString = `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 120 >> stream
BT
/F1 16 Tf
50 720 Td
(AD. Sentry Reliability Audit Report [Demo Mode]) Tj
/F1 11 Tf
0 -30 Td
(Generated dynamically for current observability evaluation.) Tj
ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000228 00000 n 
0000000399 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
470
%%EOF`;

  return new Blob([pdfString], { type: "application/pdf" });
};

// Dummy alerts for /alerts page
export const getDummyAlerts = async (): Promise<Alert[]> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  return [
    {
      id: "alt_01",
      service: "payment-api",
      title: "High Database Error Rate",
      description: "Service 'payment-api' triggered 8 database timeout exceptions in the last 10 minutes exceeding alert rule threshold (>= 3).",
      severity: "CRITICAL",
      timestamp: minutesAgo(7),
      status: "Active",
    },
    {
      id: "alt_02",
      service: "auth-service",
      title: "Repeated Auth Failure Spike",
      description: "Service 'auth-service' detected 5 failed login attempts from IP 203.0.113.42 within 60 seconds.",
      severity: "WARNING",
      timestamp: minutesAgo(14),
      status: "Active",
    },
    {
      id: "alt_03",
      service: "gateway",
      title: "Downstream Latency Threshold Exceeded",
      description: "Service 'gateway' downstream response time exceeded 1500ms threshold during peak checkout window.",
      severity: "WARNING",
      timestamp: hoursAgo(2),
      status: "Resolved",
    },
    {
      id: "alt_04",
      service: "notification-worker",
      title: "Webhook Retry Queue Backlog",
      description: "Service 'notification-worker' outbound webhook delivery experienced temporary backoff due to customer HTTP 429 response.",
      severity: "INFO",
      timestamp: hoursAgo(4),
      status: "Resolved",
    },
  ];
};

// Dummy reports for /reports page
export const getDummyReports = async (): Promise<Report[]> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  const todayStr = now.toISOString().split("T")[0];
  const lastWeekStr = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split("T")[0];

  return [
    {
      id: "rep_today",
      title: "Daily Reliability & Ingestion Audit",
      period: todayStr,
      total_events: 14892,
      incidents_count: 1,
      avg_mttr: "12m",
      service_uptime: {
        "api-gateway": "99.98%",
        database: "99.99%",
        "auth-service": "100%",
        "payment-api": "99.42%",
        "inventory-service": "99.85%",
      },
      summary:
        "Daily reliability operations normal. Transient connection lock timeout on payment-api resolved via worker pool scaling. System uptime remains within target 99.9% SLA.",
    },
    {
      id: "rep_weekly",
      title: "Weekly Observability & Health Summary",
      period: `${lastWeekStr} to ${todayStr}`,
      total_events: 104250,
      incidents_count: 3,
      avg_mttr: "15m",
      service_uptime: {
        "api-gateway": "99.95%",
        database: "99.98%",
        "auth-service": "99.99%",
        "payment-api": "99.65%",
        "inventory-service": "99.90%",
      },
      summary:
        "Weekly observability audit completed. Total throughput increased by 14% with stable p95 response times. Cache hit ratio maintained at 94.2% in Redis.",
    },
  ];
};

// Logs methods for Logs Explorer
export interface PaginatedLogs {
  data: Log[];
  limit: number;
  offset: number;
  next: string | null;
  prev: string | null;
  total: number;
}

export const getDummyLogs = async (
  service?: string,
  level?: string,
): Promise<PaginatedLogs> => {
  await new Promise((resolve) => setTimeout(resolve, 80));

  const filtered = liveLogs.filter((log) => {
    if (service && log.service !== service) return false;
    if (level && log.level !== level) return false;
    return true;
  });

  return {
    data: filtered,
    limit: 100,
    offset: 0,
    next: null,
    prev: null,
    total: filtered.length,
  };
};

export const getDummyLog = async (id: string): Promise<Log> => {
  await new Promise((resolve) => setTimeout(resolve, 40));
  const log = liveLogs.find((l) => l.id === id);
  if (!log) {
    throw new Error(`Log with id ${id} not found`);
  }
  return log;
};

export const createDummyLog = async (
  newLog: Omit<Log, "id" | "created_at">,
): Promise<Log> => {
  await new Promise((resolve) => setTimeout(resolve, 100));
  const created: Log = {
    ...newLog,
    id: `log_${Date.now().toString(36)}`,
    created_at: new Date().toISOString(),
  };
  liveLogs = [created, ...liveLogs];
  return created;
};

export const deleteDummyLog = async (id: string): Promise<{ status: string }> => {
  await new Promise((resolve) => setTimeout(resolve, 80));
  liveLogs = liveLogs.filter((l) => l.id !== id);
  return { status: "success" };
};
