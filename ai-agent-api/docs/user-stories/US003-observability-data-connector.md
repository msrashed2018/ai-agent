# US003: Observability Data Connector Framework

## Overview
**Epic**: Intelligent Infrastructure Monitoring
**Priority**: HIGH
**Complexity**: Medium
**Target Release**: v2.2

## User Story
**As a** DevOps engineer
**I want** AI agents to access real-time observability data from monitoring systems (Prometheus, Grafana, Datadog, CloudWatch)
**So that** the agent can correlate metrics, logs, and traces during investigations without manual data collection

## Current State Analysis
The service currently supports:
- ✅ MCP (Model Context Protocol) tool integration
- ✅ Bash tool for running kubectl, curl commands
- ✅ Read/Write tools for file access
- ❌ **MISSING**: Direct integration with observability platforms
- ❌ **MISSING**: Time-series data query capabilities
- ❌ **MISSING**: Metrics correlation and analysis
- ❌ **MISSING**: Log aggregation search
- ❌ **MISSING**: Distributed tracing access

## Problem Statement
When investigating incidents, agents need to ask questions like:
- "What was the CPU usage of pod X in the last hour?"
- "Show me error logs from service Y between 10:00-10:30"
- "What was the p95 latency for API endpoint Z?"
- "Find distributed traces for failed requests"

Currently, the agent must:
1. Use Bash to run `kubectl top`, `curl` to Prometheus API
2. Parse complex JSON responses manually
3. Have no context about metric names or labels
4. Cannot correlate metrics across systems

We need **native integration** with observability platforms that provides:
- Structured queries (not bash commands)
- Automatic metric discovery
- Time-range queries
- Correlation capabilities
- Anomaly detection hints

## Proposed Solution

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│              AI Agent (Claude Code)                      │
│  "Show me CPU metrics for pod X in last hour"          │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol
                       ▼
┌─────────────────────────────────────────────────────────┐
│        Observability MCP Server (New Component)         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  MCP Tools:                                       │ │
│  │  • query_metrics(query, time_range)              │ │
│  │  • search_logs(query, filters, time_range)       │ │
│  │  • get_traces(trace_id or filters)               │ │
│  │  • list_services()                                │ │
│  │  • get_service_metrics(service_name)             │ │
│  │  • correlate_metrics(metric_list, time_range)    │ │
│  │  • detect_anomalies(metric, time_range)          │ │
│  └───────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┬──────────────┐
       ▼               ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Prometheus│   │  Loki    │   │  Jaeger  │   │CloudWatch│
│ Adapter  │   │ Adapter  │   │ Adapter  │   │ Adapter  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
       │               │               │              │
       ▼               ▼               ▼              ▼
  Prometheus        Grafana        Jaeger/        AWS
  API Server        Loki           Tempo       CloudWatch
```

## Acceptance Criteria

### Core Functionality
- [ ] **AC1**: System provides MCP server for observability data access
- [ ] **AC2**: Support configuring multiple observability backends per user
- [ ] **AC3**: Agent can query time-series metrics using natural language intent
- [ ] **AC4**: Agent can search logs with text queries and filters
- [ ] **AC5**: Agent can retrieve distributed traces by ID or filters

### Metrics Integration
- [ ] **AC6**: Support Prometheus/VictoriaMetrics PromQL queries
- [ ] **AC7**: Support querying metrics by service, pod, namespace labels
- [ ] **AC8**: Return metrics as time-series data with timestamps
- [ ] **AC9**: Support metric aggregation (sum, avg, max, p95, p99)
- [ ] **AC10**: Detect anomalies in metric patterns (spikes, drops)

### Logs Integration
- [ ] **AC11**: Support Grafana Loki LogQL queries
- [ ] **AC12**: Support Elasticsearch/OpenSearch queries
- [ ] **AC13**: Filter logs by severity, service, time range
- [ ] **AC14**: Support full-text search and regex patterns
- [ ] **AC15**: Return logs with context (surrounding lines)

### Traces Integration
- [ ] **AC16**: Support Jaeger/Tempo trace queries
- [ ] **AC17**: Retrieve trace by ID or service/operation filters
- [ ] **AC18**: Show span details, durations, errors
- [ ] **AC19**: Find traces with errors or high latency
- [ ] **AC20**: Correlate traces with logs and metrics

### Multi-Source Correlation
- [ ] **AC21**: Query metrics from multiple namespaces simultaneously
- [ ] **AC22**: Correlate metrics and logs by timestamp
- [ ] **AC23**: Link metrics to related traces
- [ ] **AC24**: Compare metrics across different time windows
- [ ] **AC25**: Detect correlated anomalies across services

### Security & Performance
- [ ] **AC26**: Each user configures their own observability credentials
- [ ] **AC27**: Queries are rate-limited to prevent abuse
- [ ] **AC28**: Large result sets are paginated or sampled
- [ ] **AC29**: Queries timeout after configurable duration (default: 30s)
- [ ] **AC30**: Credentials are encrypted at rest

## Database Schema Changes

### New Table: `observability_connections`
```sql
CREATE TABLE observability_connections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Backend type
    backend_type VARCHAR(50) NOT NULL,  -- 'prometheus', 'loki', 'jaeger', 'cloudwatch', 'datadog'

    -- Connection config
    connection_config JSONB NOT NULL,
    /*
    Example configs:

    Prometheus:
    {
      "url": "http://prometheus.monitoring.svc:9090",
      "auth": {
        "type": "bearer",  # or "basic", "none"
        "token": "encrypted_token"
      },
      "timeout_seconds": 30,
      "query_limits": {
        "max_samples": 10000,
        "max_time_range_hours": 24
      }
    }

    Loki:
    {
      "url": "http://loki.monitoring.svc:3100",
      "auth": {...},
      "default_limit": 1000,
      "max_limit": 5000
    }

    Jaeger:
    {
      "url": "http://jaeger-query.tracing.svc:16686",
      "auth": {...}
    }

    CloudWatch:
    {
      "region": "us-east-1",
      "access_key_id": "encrypted_key",
      "secret_access_key": "encrypted_secret",
      "namespaces": ["AWS/EC2", "AWS/RDS"]
    }

    Datadog:
    {
      "site": "datadoghq.com",
      "api_key": "encrypted_key",
      "app_key": "encrypted_app_key"
    }
    */

    -- Metadata
    is_enabled BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,   -- Default connection for this backend type
    tags JSONB,

    -- Health check
    last_health_check_at TIMESTAMP,
    health_status VARCHAR(50),          -- 'healthy', 'degraded', 'unhealthy', 'unknown'
    health_error TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_observability_connections_user_id (user_id),
    INDEX idx_observability_connections_backend_type (backend_type),
    UNIQUE INDEX idx_observability_connections_user_backend_default (user_id, backend_type, is_default) WHERE is_default = true
);
```

### New Table: `observability_query_cache`
```sql
CREATE TABLE observability_query_cache (
    id UUID PRIMARY KEY,
    connection_id UUID NOT NULL REFERENCES observability_connections(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL,    -- SHA256 of normalized query

    -- Query
    query_type VARCHAR(50),             -- 'metrics', 'logs', 'traces'
    query_text TEXT,
    query_params JSONB,

    -- Result
    result_data JSONB,
    result_count INT,

    -- Cache metadata
    cached_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,      -- TTL-based expiration
    hit_count INT DEFAULT 0,

    INDEX idx_observability_query_cache_connection_id (connection_id),
    INDEX idx_observability_query_cache_query_hash (query_hash),
    INDEX idx_observability_query_cache_expires_at (expires_at)
);
```

### New Table: `observability_query_history`
```sql
CREATE TABLE observability_query_history (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id UUID NOT NULL REFERENCES observability_connections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),

    -- Query
    query_type VARCHAR(50),
    query_text TEXT,
    query_params JSONB,

    -- Results
    result_count INT,
    result_sample JSONB,                -- First 10 results for preview
    error_message TEXT,

    -- Performance
    execution_time_ms INT,
    was_cached BOOLEAN DEFAULT false,

    queried_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_observability_query_history_session_id (session_id),
    INDEX idx_observability_query_history_user_id (user_id),
    INDEX idx_observability_query_history_queried_at (queried_at)
);
```

## MCP Tools Specification

### Tool: `query_metrics`
```typescript
{
  name: "query_metrics",
  description: "Query time-series metrics from Prometheus/VictoriaMetrics",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "PromQL query or natural language query"
        // Example: "rate(http_requests_total[5m])"
        // Example: "CPU usage for pod web-app-xyz"
      },
      time_range: {
        type: "object",
        properties: {
          start: { type: "string" },  // ISO 8601 or relative: "1h", "30m"
          end: { type: "string" }      // Optional, defaults to "now"
        }
      },
      connection_id: {
        type: "string",
        description: "Optional: specific connection to use"
      },
      aggregation: {
        type: "string",
        enum: ["avg", "sum", "max", "min", "p95", "p99"]
      }
    },
    required: ["query"]
  }
}

Response:
{
  "results": [
    {
      "metric": {
        "pod": "web-app-xyz",
        "namespace": "production"
      },
      "values": [
        [1729425600, "0.95"],  // [timestamp, value]
        [1729425660, "1.02"],
        ...
      ]
    }
  ],
  "query_executed": "rate(container_cpu_usage_seconds_total{pod=\"web-app-xyz\"}[5m])",
  "query_time_ms": 145
}
```

### Tool: `search_logs`
```typescript
{
  name: "search_logs",
  description: "Search logs from Loki, Elasticsearch, or CloudWatch Logs",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Log search query or text pattern"
      },
      filters: {
        type: "object",
        properties: {
          service: { type: "string" },
          namespace: { type: "string" },
          severity: {
            type: "string",
            enum: ["error", "warn", "info", "debug"]
          },
          pod: { type: "string" }
        }
      },
      time_range: {
        type: "object",
        properties: {
          start: { type: "string" },
          end: { type: "string" }
        }
      },
      limit: {
        type: "number",
        default: 100,
        maximum: 1000
      },
      context_lines: {
        type: "number",
        description: "Include N lines before/after each match",
        default: 0,
        maximum: 10
      }
    },
    required: ["query"]
  }
}

Response:
{
  "logs": [
    {
      "timestamp": "2025-10-20T10:30:15.123Z",
      "level": "error",
      "service": "web-app",
      "pod": "web-app-xyz",
      "message": "OutOfMemoryError: Java heap space",
      "context": {
        "before": ["..."],
        "after": ["..."]
      },
      "labels": {
        "namespace": "production",
        "container": "app"
      }
    }
  ],
  "total_count": 245,
  "returned_count": 100,
  "query_time_ms": 234
}
```

### Tool: `get_traces`
```typescript
{
  name: "get_traces",
  description: "Retrieve distributed traces from Jaeger/Tempo",
  inputSchema: {
    type: "object",
    properties: {
      trace_id: {
        type: "string",
        description: "Specific trace ID"
      },
      filters: {
        type: "object",
        properties: {
          service: { type: "string" },
          operation: { type: "string" },
          min_duration: { type: "string" },  // "100ms", "1s"
          max_duration: { type: "string" },
          tags: { type: "object" },  // {"http.status_code": "500"}
          has_error: { type: "boolean" }
        }
      },
      time_range: { type: "object" },
      limit: { type: "number", default: 20 }
    }
  }
}

Response:
{
  "traces": [
    {
      "trace_id": "abc123xyz",
      "spans": [
        {
          "span_id": "span1",
          "operation_name": "HTTP GET /api/users",
          "service_name": "api-gateway",
          "start_time": "2025-10-20T10:30:15.000Z",
          "duration_ms": 245,
          "tags": {
            "http.method": "GET",
            "http.status_code": "500"
          },
          "logs": [...],
          "references": [...]
        }
      ],
      "duration_ms": 245,
      "has_error": true,
      "service_count": 3
    }
  ],
  "total_count": 15
}
```

### Tool: `detect_anomalies`
```typescript
{
  name: "detect_anomalies",
  description: "Detect anomalies in metric time-series using statistical methods",
  inputSchema: {
    type: "object",
    properties: {
      metric_query: { type: "string" },
      time_range: { type: "object" },
      sensitivity: {
        type: "string",
        enum: ["low", "medium", "high"],
        default: "medium"
      },
      method: {
        type: "string",
        enum: ["zscore", "iqr", "isolation_forest", "auto"],
        default: "auto"
      }
    }
  }
}

Response:
{
  "anomalies_detected": true,
  "anomalies": [
    {
      "timestamp": "2025-10-20T10:25:00Z",
      "value": 95.5,
      "expected_range": [10, 30],
      "deviation_score": 8.5,
      "severity": "high",
      "description": "CPU usage spike: 3.2x higher than normal"
    }
  ],
  "baseline_stats": {
    "mean": 15.2,
    "std_dev": 3.4,
    "p95": 22.1
  }
}
```

## Implementation Tasks

### Phase 1: Core Framework (Sprint 1-2)
1. **Create database schema** (observability_connections table)
2. **Implement ObservabilityConnection entity** and repository
3. **Create BaseObservabilityAdapter** abstract class
4. **Implement connection management** service (CRUD)
5. **Add credential encryption** for API keys/tokens
6. **Create health check** mechanism for connections

### Phase 2: Prometheus Integration (Sprint 3)
7. **Implement PrometheusAdapter** with PromQL support
8. **Create `query_metrics` MCP tool**
9. **Add metric discovery** (list available metrics)
10. **Implement query result caching**
11. **Add query history** tracking
12. **Create natural language to PromQL** converter (basic)

### Phase 3: Logs Integration (Sprint 4)
13. **Implement LokiAdapter** for Grafana Loki
14. **Create `search_logs` MCP tool**
15. **Add log filtering** by service, severity, time
16. **Implement context lines** retrieval
17. **Add log aggregation** (count by severity)
18. **Create ElasticsearchAdapter** (optional)

### Phase 4: Traces Integration (Sprint 5)
19. **Implement JaegerAdapter** for distributed tracing
20. **Create `get_traces` MCP tool**
21. **Add trace filtering** (by service, duration, errors)
22. **Implement span details** retrieval
23. **Add trace-to-logs correlation**
24. **Create TempoAdapter** (optional)

### Phase 5: Advanced Features (Sprint 6)
25. **Implement `detect_anomalies` tool** with statistical methods
26. **Add metric correlation** analysis
27. **Create `compare_time_windows` tool**
28. **Implement CloudWatch adapter**
29. **Add Datadog adapter**
30. **Create query optimization** hints

### Phase 6: MCP Server Deployment (Sprint 7)
31. **Package as standalone MCP server**
32. **Create Docker image** for MCP server
33. **Add configuration management** (YAML/JSON)
34. **Implement connection pooling** for backends
35. **Add monitoring metrics** for MCP server itself
36. **Create deployment guide**

## API Endpoints

### Connection Management
```http
POST /api/v1/observability/connections
GET /api/v1/observability/connections
GET /api/v1/observability/connections/{connection_id}
PUT /api/v1/observability/connections/{connection_id}
DELETE /api/v1/observability/connections/{connection_id}
POST /api/v1/observability/connections/{connection_id}/test  # Health check
```

### Query History
```http
GET /api/v1/observability/query-history?session_id={session_id}
GET /api/v1/observability/query-history/{query_id}
```

## Example Usage in Investigation

### Scenario: High CPU Alert Investigation
```markdown
**Agent**: I'll investigate the high CPU alert for pod web-app-xyz.

**Step 1: Query current CPU metrics**
[Uses query_metrics tool]
query_metrics({
  query: "CPU usage for pod web-app-xyz in last 1 hour",
  time_range: { start: "1h" }
})

**Result**: CPU spiked from 20% to 95% at 10:25 AM

**Step 2: Check for errors in logs**
[Uses search_logs tool]
search_logs({
  query: "error OR exception",
  filters: { pod: "web-app-xyz", severity: "error" },
  time_range: { start: "10:20", end: "10:30" },
  limit: 100
})

**Result**: Found OutOfMemoryError at 10:24:55 AM

**Step 3: Get related traces**
[Uses get_traces tool]
get_traces({
  filters: {
    service: "web-app",
    has_error: true,
    min_duration: "5s"
  },
  time_range: { start: "10:20", end: "10:30" }
})

**Result**: Several slow requests with memory allocation failures

**Step 4: Correlate with deployment events**
[Uses query_metrics tool for deployment markers]

**Conclusion**: Memory leak introduced in version 2.5 deployed at 10:20 AM.
Recommendation: Rollback to version 2.4.
```

## Success Metrics
- **Query response time**: < 2 seconds for P95
- **Cache hit rate**: > 70% for repeated queries
- **Connection health**: > 99% uptime
- **Agent query success rate**: > 95%
- **Data freshness**: < 30 seconds lag from source

## Future Enhancements
- AI-powered query suggestion (based on investigation context)
- Automatic correlation of metrics, logs, and traces
- Predictive anomaly detection using ML models
- Custom dashboards generated from agent queries
- Integration with APM platforms (New Relic, AppDynamics)

## Related Documentation
- `/docs/components/mcp/MCP_OVERVIEW.md` - MCP integration
- `/docs/user-stories/US001-event-driven-triggers.md` - Event triggers
- `/docs/user-stories/US002-incident-investigation-workflow.md` - Workflows

---

**Created**: 2025-10-20
**Author**: AI Architecture Analysis
**Status**: PROPOSED
**Review Status**: Pending
