# US001: Event-Driven Agent Triggers

## Overview
**Epic**: Reactive Infrastructure Monitoring
**Priority**: HIGH
**Complexity**: Medium
**Target Release**: v2.0

## User Story
**As a** DevOps engineer
**I want** AI agents to be automatically triggered by external events (alerts, webhooks, monitoring systems)
**So that** the agent can investigate issues immediately when they occur, without human intervention

## Current State Analysis
The service currently supports:
- ✅ Manual task execution via API (`POST /api/v1/tasks/{task_id}/execute`)
- ✅ Scheduled tasks with cron expressions
- ✅ Session creation and message sending
- ❌ **MISSING**: Webhook endpoints to receive external events
- ❌ **MISSING**: Event queue/broker integration
- ❌ **MISSING**: Event-to-task mapping configuration
- ❌ **MISSING**: Event history and audit trail

## Problem Statement
Currently, the AI agent operates in "push" mode only - users must create tasks to instruct the LLM. For infrastructure monitoring, we need "pull" mode where:
1. Prometheus sends an alert when CPU > 90%
2. Kubernetes emits event when pod crashes
3. Application logging system detects error spike
4. External monitoring system detects anomaly

In all these cases, the agent should **automatically react** without human intervention.

## Proposed Solution

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│         External Event Sources                          │
├─────────────────────────────────────────────────────────┤
│  Prometheus  │  Kubernetes  │  CloudWatch  │  Custom    │
│  AlertManager│  Events API  │  Alarms      │  Webhooks  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬─────┘
       │              │              │              │
       │  HTTP POST   │  HTTP POST   │  HTTP POST   │
       ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              Event Ingestion API                         │
│  POST /api/v1/events/webhook/{webhook_id}              │
│  POST /api/v1/events/prometheus                        │
│  POST /api/v1/events/kubernetes                        │
│  POST /api/v1/events/custom                            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Event Processor Service                     │
│  • Validate event schema                               │
│  • Enrich with metadata                                │
│  • Apply filters & routing rules                       │
│  • Rate limiting & deduplication                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           Event-to-Trigger Mapping Engine               │
│  • Match event to trigger rules                        │
│  • Extract context variables                           │
│  • Determine task to execute                           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Task Execution Service                      │
│  • Create session from template                        │
│  • Render prompt with event data                       │
│  • Execute investigation                               │
│  • Generate RCA report                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           Notification & Response System                 │
│  • Send report to Slack/PagerDuty/Email                │
│  • Update incident tracking system                     │
│  • Create follow-up actions                            │
└─────────────────────────────────────────────────────────┘
```

## Acceptance Criteria

### Core Functionality
- [ ] **AC1**: System accepts webhook POST requests with configurable authentication (HMAC, Bearer, API Key)
- [ ] **AC2**: Users can create "Event Triggers" that map event patterns to tasks
- [ ] **AC3**: Event data is accessible in task prompt templates via variables
- [ ] **AC4**: System deduplicates identical events within configurable time window
- [ ] **AC5**: Failed event processing retries with exponential backoff
- [ ] **AC6**: All events are logged with full payload for audit

### Event Sources
- [ ] **AC7**: Support Prometheus AlertManager webhook format
- [ ] **AC8**: Support Kubernetes event webhook format
- [ ] **AC9**: Support AWS CloudWatch Alarm SNS format
- [ ] **AC10**: Support generic JSON webhook with JSON path selectors
- [ ] **AC11**: Support event filtering by severity, labels, annotations

### Security & Control
- [ ] **AC12**: Webhook endpoints require authentication (configurable per webhook)
- [ ] **AC13**: Rate limiting per webhook (configurable: 100 events/minute default)
- [ ] **AC14**: Event payload size limit (1MB default)
- [ ] **AC15**: IP whitelisting support for webhook sources
- [ ] **AC16**: Events can be quarantined for manual review if suspicious

### Integration & Response
- [ ] **AC17**: Agent can access event context in session (via MCP or environment)
- [ ] **AC18**: Investigation results can trigger callbacks to external systems
- [ ] **AC19**: Support notification to Slack/Teams/PagerDuty after investigation
- [ ] **AC20**: Support creating follow-up tasks based on investigation findings

## Database Schema Changes

### New Table: `event_triggers`
```sql
CREATE TABLE event_triggers (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Event matching
    event_source VARCHAR(100) NOT NULL, -- 'prometheus', 'kubernetes', 'cloudwatch', 'custom'
    event_type_filter VARCHAR(255),     -- Optional: filter by event type
    severity_filter JSONB,              -- ['critical', 'warning']
    label_selectors JSONB,              -- Key-value pairs for matching
    json_path_conditions JSONB,         -- Advanced filtering

    -- Task execution
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    session_template_id UUID REFERENCES session_templates(id),
    prompt_template TEXT,               -- Override task prompt with event data

    -- Behavior
    is_enabled BOOLEAN DEFAULT true,
    cooldown_seconds INT DEFAULT 300,   -- Prevent duplicate triggers
    max_executions_per_hour INT DEFAULT 10,

    -- Actions
    notification_config JSONB,          -- Where to send results
    callback_webhook_url TEXT,          -- POST results here

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_event_triggers_user_id (user_id),
    INDEX idx_event_triggers_event_source (event_source),
    INDEX idx_event_triggers_is_enabled (is_enabled)
);
```

### New Table: `event_logs`
```sql
CREATE TABLE event_logs (
    id UUID PRIMARY KEY,
    event_trigger_id UUID REFERENCES event_triggers(id) ON DELETE CASCADE,

    -- Event data
    event_source VARCHAR(100) NOT NULL,
    event_type VARCHAR(255),
    event_payload JSONB NOT NULL,       -- Full event data
    event_fingerprint VARCHAR(64),      -- For deduplication

    -- Processing
    status VARCHAR(50) NOT NULL,        -- 'received', 'matched', 'triggered', 'ignored', 'failed'
    matched_trigger_ids JSONB,          -- Array of trigger IDs that matched
    processing_error TEXT,

    -- Execution
    task_execution_id UUID REFERENCES task_executions(id),
    session_id UUID REFERENCES sessions(id),

    -- Metadata
    source_ip VARCHAR(45),
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,

    INDEX idx_event_logs_event_source (event_source),
    INDEX idx_event_logs_status (status),
    INDEX idx_event_logs_received_at (received_at),
    INDEX idx_event_logs_fingerprint (event_fingerprint)
);
```

### Extended: `task_executions`
```sql
ALTER TABLE task_executions ADD COLUMN trigger_event_id UUID REFERENCES event_logs(id);
ALTER TABLE task_executions ADD COLUMN event_context JSONB; -- Event data for reference
```

## API Endpoints

### Event Ingestion
```http
POST /api/v1/events/webhook/{webhook_id}
Authorization: Bearer {token} OR X-Webhook-Secret: {secret}
Content-Type: application/json

{
  "event_type": "alert",
  "severity": "critical",
  "labels": {
    "alertname": "HighCPU",
    "instance": "prod-web-01",
    "namespace": "production"
  },
  "annotations": {
    "summary": "CPU usage above 90% for 5 minutes",
    "description": "..."
  },
  "timestamp": "2025-10-20T10:30:00Z",
  "value": 94.5
}

Response 202 Accepted:
{
  "event_id": "uuid",
  "status": "received",
  "matched_triggers": 2,
  "executions_started": 1
}
```

### Trigger Management
```http
POST /api/v1/event-triggers
GET /api/v1/event-triggers
GET /api/v1/event-triggers/{trigger_id}
PUT /api/v1/event-triggers/{trigger_id}
DELETE /api/v1/event-triggers/{trigger_id}
POST /api/v1/event-triggers/{trigger_id}/test  # Simulate event
```

### Event History
```http
GET /api/v1/events?source=prometheus&status=triggered&limit=100
GET /api/v1/events/{event_id}
GET /api/v1/events/{event_id}/executions
```

## Implementation Tasks

### Phase 1: Core Infrastructure (Sprint 1-2)
1. **Create database schema** (event_triggers, event_logs tables)
2. **Implement Event Ingestion API** (`/api/v1/events/webhook`)
3. **Create EventTrigger domain entity & repository**
4. **Create EventLog domain entity & repository**
5. **Implement basic webhook authentication** (Bearer, HMAC)
6. **Create EventProcessorService** with validation & persistence

### Phase 2: Matching & Execution (Sprint 3-4)
7. **Implement Event Matching Engine** (label selectors, filters)
8. **Create EventTriggerService** for CRUD operations
9. **Integrate with TaskService** for automatic execution
10. **Implement deduplication** using event fingerprinting
11. **Add rate limiting** per trigger
12. **Implement cooldown** mechanism

### Phase 3: Event Sources (Sprint 5)
13. **Add Prometheus AlertManager webhook handler**
14. **Add Kubernetes event webhook handler**
15. **Add AWS CloudWatch SNS handler**
16. **Implement JSON path filtering** for generic webhooks

### Phase 4: Notifications & Callbacks (Sprint 6)
17. **Implement notification service** (Slack, Teams, Email)
18. **Add callback webhook** support for results
19. **Create PagerDuty integration** for incident updates
20. **Implement event-to-investigation-to-notification flow**

### Phase 5: Monitoring & Observability (Sprint 7)
21. **Add Prometheus metrics** for events (received, matched, failed)
22. **Create event dashboard** API endpoints
23. **Add event replay** capability for testing
24. **Implement audit logging** for all event processing

## Example Use Cases

### Use Case 1: Kubernetes Pod Crash Investigation
```yaml
event_trigger:
  name: "Pod Crash Auto-Investigator"
  event_source: kubernetes
  event_type_filter: "Warning"
  label_selectors:
    reason: "CrashLoopBackOff"
    namespace: "production"
  task_id: "investigate-pod-crash-task"
  prompt_template: |
    A pod has crashed in production. Please investigate:

    Pod: {{event.involvedObject.name}}
    Namespace: {{event.involvedObject.namespace}}
    Reason: {{event.reason}}
    Message: {{event.message}}

    Steps:
    1. Get pod logs (last 100 lines)
    2. Check recent events for this pod
    3. Inspect pod description for resource issues
    4. Analyze root cause
    5. Provide fix recommendations
  notification_config:
    slack:
      channel: "#production-alerts"
      mention: "@sre-oncall"
```

### Use Case 2: High CPU Alert from Prometheus
```yaml
event_trigger:
  name: "High CPU Investigation"
  event_source: prometheus
  label_selectors:
    alertname: "HighCPU"
    severity: "critical"
  task_id: "investigate-high-cpu-task"
  prompt_template: |
    CPU alert triggered for {{event.labels.instance}}
    Current value: {{event.value}}%

    Investigate:
    1. Check top processes consuming CPU
    2. Review recent deployments
    3. Check for memory leaks
    4. Provide mitigation steps
  cooldown_seconds: 600  # Don't trigger again for 10 minutes
```

## Technical Considerations

### Deduplication Strategy
- Calculate event fingerprint: `SHA256(event_source + event_type + key_labels)`
- Store last 1 hour of fingerprints in Redis
- Skip execution if duplicate found within cooldown period

### Rate Limiting
- Per webhook: 100 requests/minute (configurable)
- Per trigger: max_executions_per_hour (default: 10)
- Global: 1000 events/minute across all webhooks

### Security
- Webhook endpoints require authentication
- Support HMAC signature verification (GitHub/Slack style)
- IP whitelisting for known sources
- Payload size limits to prevent DOS

### Scalability
- Events are processed asynchronously (Celery queue)
- Webhook endpoint returns 202 Accepted immediately
- Support horizontal scaling of event processors
- Redis for distributed deduplication

## Dependencies
- Existing TaskService for execution
- Existing SessionService for agent interaction
- Celery for async processing
- Redis for deduplication cache
- Notification libraries (slack-sdk, boto3 for SNS)

## Risks & Mitigation
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Event flood DOS | HIGH | MEDIUM | Rate limiting, queue backpressure, circuit breakers |
| Incorrect event routing | HIGH | LOW | Test mode, dry-run capability, event replay |
| Trigger execution loops | MEDIUM | LOW | Cooldown periods, max executions per hour |
| Webhook auth bypass | HIGH | LOW | Strong auth, IP whitelisting, audit logging |

## Success Metrics
- **Event processing latency**: < 500ms from receipt to trigger matching
- **Execution trigger time**: < 5 seconds from event to session creation
- **False positive rate**: < 5% (events matched but not relevant)
- **Deduplication effectiveness**: > 95% of duplicate events suppressed
- **Uptime**: 99.9% availability for webhook endpoints

## Future Enhancements
- Visual event trigger builder UI
- Event correlation (group related events)
- ML-based event severity classification
- Auto-tuning of trigger thresholds
- Integration with incident management platforms (Jira, ServiceNow)

## Related Documentation
- `/docs/components/tasks/TASK_AUTOMATION.md` - Existing task system
- `/docs/architecture/DATA_FLOW.md` - Request flow patterns
- `/docs/components/claude_sdk/HOOK_SYSTEM.md` - Hook system for notifications

---

**Created**: 2025-10-20
**Author**: AI Architecture Analysis
**Status**: PROPOSED
**Review Status**: Pending
