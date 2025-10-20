# US002: Incident Investigation Workflow Engine

## Overview
**Epic**: Automated RCA (Root Cause Analysis)
**Priority**: HIGH
**Complexity**: High
**Target Release**: v2.1

## User Story
**As a** DevOps/SRE engineer
**I want** a structured workflow for AI-driven incident investigation with checkpoints and human review
**So that** complex incidents are investigated systematically with the ability to intervene and guide the agent

## Current State Analysis
The service currently supports:
- ✅ Session-based conversations with Claude
- ✅ Task execution with prompt templates
- ✅ Report generation
- ❌ **MISSING**: Multi-step workflow orchestration
- ❌ **MISSING**: Human approval checkpoints
- ❌ **MISSING**: Workflow state persistence
- ❌ **MISSING**: Decision trees and branching logic
- ❌ **MISSING**: Rollback/retry mechanisms

## Problem Statement
Infrastructure incidents often require multi-step investigation:
1. **Detect** - Identify the problem
2. **Gather** - Collect logs, metrics, system state
3. **Analyze** - Correlate data, find patterns
4. **Hypothesize** - Form root cause theories
5. **Validate** - Test hypotheses
6. **Remediate** - Apply fix (with human approval)
7. **Verify** - Confirm resolution
8. **Document** - Generate RCA report

Currently, this requires multiple manual API calls or a single long-running session without structure. We need a workflow engine that:
- Orchestrates multi-step investigations
- Allows human checkpoints for critical decisions
- Maintains investigation state across steps
- Supports branching based on findings
- Enables rollback if needed

## Proposed Solution

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│          Workflow Definition (YAML/JSON)                │
│  name: "K8s Pod Crash Investigation"                   │
│  steps:                                                │
│    1. detect_issue                                     │
│    2. gather_logs                                      │
│    3. analyze_patterns                                 │
│    4. [human_review] ← checkpoint                      │
│    5. apply_fix                                        │
│    6. verify_resolution                                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          Workflow Engine Service                        │
│  • Parse workflow definition                           │
│  • Manage workflow execution state                     │
│  • Handle step transitions                             │
│  • Execute agent interactions                          │
│  • Manage checkpoints & approvals                      │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────┐   ┌────────────┐   ┌─────────────┐
│  Agent  │   │  Human     │   │  External   │
│  Step   │   │  Approval  │   │  Tools      │
│         │   │  Required  │   │  (kubectl)  │
└─────────┘   └────────────┘   └─────────────┘
```

## Acceptance Criteria

### Workflow Definition
- [ ] **AC1**: Users can define workflows in YAML/JSON format
- [ ] **AC2**: Workflows support sequential steps with dependencies
- [ ] **AC3**: Workflows support conditional branching (if-else logic)
- [ ] **AC4**: Workflows support parallel step execution
- [ ] **AC5**: Each step specifies: prompt, tools allowed, timeout, retry policy

### Execution & State
- [ ] **AC6**: Workflow execution creates a persistent state machine
- [ ] **AC7**: State includes: current step, step history, collected data, decisions
- [ ] **AC8**: Users can pause/resume workflow execution
- [ ] **AC9**: Failed steps can be retried without restarting workflow
- [ ] **AC10**: Workflow can be canceled at any step

### Human Checkpoints
- [ ] **AC11**: Workflows support human approval checkpoints
- [ ] **AC12**: System sends notification when checkpoint reached (Slack/Email)
- [ ] **AC13**: Humans can approve, reject, or request modifications
- [ ] **AC14**: Rejection allows custom feedback to guide next steps
- [ ] **AC15**: Timeout on approvals with configurable default action

### Data Flow & Context
- [ ] **AC16**: Outputs from previous steps are accessible in subsequent steps
- [ ] **AC17**: Workflow maintains investigation context (variables, findings)
- [ ] **AC18**: Steps can update shared workflow state
- [ ] **AC19**: Final step generates structured RCA report
- [ ] **AC20**: All step outputs are preserved for audit

### Integration
- [ ] **AC21**: Workflows can be triggered by events (US001)
- [ ] **AC22**: Workflows can trigger external webhooks at checkpoints
- [ ] **AC23**: Workflows integrate with existing MCP tools
- [ ] **AC24**: Support custom Python/JavaScript steps for advanced logic

## Database Schema Changes

### New Table: `workflow_definitions`
```sql
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version INT DEFAULT 1,

    -- Definition
    workflow_spec JSONB NOT NULL,       -- Full workflow definition
    /*
    Example spec:
    {
      "steps": [
        {
          "id": "detect",
          "type": "agent",
          "prompt_template": "Analyze the alert: {{event.summary}}",
          "allowed_tools": ["Read", "Bash"],
          "timeout_seconds": 300,
          "retry_policy": {"max_attempts": 3, "backoff": "exponential"},
          "on_success": "gather_logs",
          "on_failure": "notify_sre"
        },
        {
          "id": "gather_logs",
          "type": "agent",
          "prompt_template": "Collect logs for {{context.pod_name}}",
          ...
        },
        {
          "id": "human_review",
          "type": "checkpoint",
          "message": "Review findings and approve remediation",
          "timeout_seconds": 3600,
          "on_approve": "apply_fix",
          "on_reject": "escalate",
          "on_timeout": "escalate"
        }
      ],
      "variables": {
        "max_log_lines": 1000,
        "namespace": "production"
      }
    }
    */

    -- Metadata
    category VARCHAR(100),              -- 'incident', 'investigation', 'remediation'
    tags JSONB,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_workflow_definitions_user_id (user_id),
    INDEX idx_workflow_definitions_category (category)
);
```

### New Table: `workflow_executions`
```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    workflow_definition_id UUID NOT NULL REFERENCES workflow_definitions(id),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Trigger
    trigger_type VARCHAR(50),           -- 'manual', 'event', 'scheduled'
    trigger_event_id UUID REFERENCES event_logs(id),

    -- State
    status VARCHAR(50) NOT NULL,        -- 'running', 'waiting_approval', 'paused', 'completed', 'failed', 'canceled'
    current_step_id VARCHAR(255),
    current_step_index INT,

    -- Context
    workflow_context JSONB,             -- Variables, findings, decisions
    /*
    Example context:
    {
      "variables": {
        "pod_name": "web-app-xyz",
        "namespace": "production"
      },
      "findings": {
        "error_pattern": "OutOfMemory",
        "frequency": 15,
        "affected_pods": ["web-app-xyz", "web-app-abc"]
      },
      "decisions": {
        "root_cause": "Memory leak in app version 2.5",
        "remediation": "Rollback to version 2.4"
      }
    }
    */

    -- Execution tracking
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms BIGINT,
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_workflow_executions_workflow_def_id (workflow_definition_id),
    INDEX idx_workflow_executions_user_id (user_id),
    INDEX idx_workflow_executions_status (status)
);
```

### New Table: `workflow_step_executions`
```sql
CREATE TABLE workflow_step_executions (
    id UUID PRIMARY KEY,
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,

    -- Step identification
    step_id VARCHAR(255) NOT NULL,
    step_index INT NOT NULL,
    step_type VARCHAR(50) NOT NULL,     -- 'agent', 'checkpoint', 'webhook', 'script'

    -- Session (for agent steps)
    session_id UUID REFERENCES sessions(id),

    -- Status
    status VARCHAR(50) NOT NULL,        -- 'pending', 'running', 'waiting_approval', 'completed', 'failed', 'skipped'
    retry_count INT DEFAULT 0,

    -- Input/Output
    step_input JSONB,                   -- Input data for this step
    step_output JSONB,                  -- Output/result from this step
    error_message TEXT,

    -- Human approval (for checkpoint steps)
    approval_status VARCHAR(50),        -- 'pending', 'approved', 'rejected', 'timeout'
    approval_decision_by UUID REFERENCES users(id),
    approval_decision_at TIMESTAMP,
    approval_feedback TEXT,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms BIGINT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_workflow_step_executions_workflow_execution_id (workflow_execution_id),
    INDEX idx_workflow_step_executions_status (status),
    INDEX idx_workflow_step_executions_approval_status (approval_status)
);
```

### New Table: `workflow_notifications`
```sql
CREATE TABLE workflow_notifications (
    id UUID PRIMARY KEY,
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    workflow_step_execution_id UUID REFERENCES workflow_step_executions(id),

    notification_type VARCHAR(50),      -- 'checkpoint', 'failure', 'completion'
    channel VARCHAR(50),                -- 'slack', 'email', 'pagerduty', 'webhook'
    recipient TEXT,
    message TEXT,
    metadata JSONB,

    status VARCHAR(50),                 -- 'pending', 'sent', 'failed'
    sent_at TIMESTAMP,
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_workflow_notifications_workflow_execution_id (workflow_execution_id),
    INDEX idx_workflow_notifications_status (status)
);
```

## API Endpoints

### Workflow Definition Management
```http
POST /api/v1/workflows
GET /api/v1/workflows
GET /api/v1/workflows/{workflow_id}
PUT /api/v1/workflows/{workflow_id}
DELETE /api/v1/workflows/{workflow_id}
POST /api/v1/workflows/{workflow_id}/validate  # Validate workflow spec
```

### Workflow Execution
```http
POST /api/v1/workflows/{workflow_id}/execute
GET /api/v1/workflow-executions
GET /api/v1/workflow-executions/{execution_id}
POST /api/v1/workflow-executions/{execution_id}/pause
POST /api/v1/workflow-executions/{execution_id}/resume
POST /api/v1/workflow-executions/{execution_id}/cancel
GET /api/v1/workflow-executions/{execution_id}/steps
POST /api/v1/workflow-executions/{execution_id}/retry-step/{step_id}
```

### Checkpoint Approvals
```http
GET /api/v1/workflow-executions/{execution_id}/pending-approvals
POST /api/v1/workflow-executions/{execution_id}/approve-step/{step_id}
POST /api/v1/workflow-executions/{execution_id}/reject-step/{step_id}
```

### Monitoring
```http
GET /api/v1/workflow-executions/active      # All running workflows
GET /api/v1/workflow-executions/statistics  # Completion rates, avg duration
```

## Example Workflow Definition

### Kubernetes Pod Crash Investigation
```yaml
name: "K8s Pod Crash RCA Workflow"
description: "Systematic investigation of pod crashes"
version: 1
category: incident

variables:
  max_log_lines: 1000
  lookback_hours: 24

steps:
  # Step 1: Detect and understand the issue
  - id: detect_issue
    type: agent
    description: "Analyze the crash event and identify key information"
    prompt_template: |
      A pod has crashed. Analyze the following event:

      {{event.payload}}

      Extract and summarize:
      1. Pod name and namespace
      2. Container that crashed
      3. Exit code and reason
      4. Timestamp
      5. Any error messages
    allowed_tools: []  # No tools needed, just analysis
    timeout_seconds: 120
    on_success: gather_pod_status
    on_failure: notify_failure

  # Step 2: Gather current pod status
  - id: gather_pod_status
    type: agent
    prompt_template: |
      Get the current status of pod {{context.findings.pod_name}} in namespace {{context.findings.namespace}}

      Commands to run:
      1. kubectl describe pod {{context.findings.pod_name}} -n {{context.findings.namespace}}
      2. kubectl get events -n {{context.findings.namespace}} --field-selector involvedObject.name={{context.findings.pod_name}}
    allowed_tools: ["Bash"]
    timeout_seconds: 300
    on_success: gather_logs
    on_failure: gather_logs  # Continue even if this fails

  # Step 3: Collect logs
  - id: gather_logs
    type: agent
    prompt_template: |
      Collect logs from the crashed container:

      1. Previous container logs: kubectl logs {{context.findings.pod_name}} -n {{context.findings.namespace}} --previous --tail={{variables.max_log_lines}}
      2. Current container logs if running: kubectl logs {{context.findings.pod_name}} -n {{context.findings.namespace}} --tail={{variables.max_log_lines}}

      Look for error patterns, stack traces, and anomalies
    allowed_tools: ["Bash"]
    timeout_seconds: 300
    on_success: analyze_patterns
    on_failure: notify_failure

  # Step 4: Pattern analysis and correlation
  - id: analyze_patterns
    type: agent
    prompt_template: |
      Analyze all gathered data:

      Pod Status:
      {{context.step_outputs.gather_pod_status}}

      Logs:
      {{context.step_outputs.gather_logs}}

      Tasks:
      1. Identify error patterns in logs
      2. Check for resource constraints (OOMKilled, CPU throttling)
      3. Look for application errors or exceptions
      4. Check for configuration issues
      5. Review recent deployments or changes
      6. Correlate with similar incidents

      Provide a detailed analysis with:
      - Error patterns found
      - Frequency and timing
      - Potential root causes (ranked by likelihood)
    allowed_tools: ["Bash", "Read"]
    timeout_seconds: 600
    on_success: formulate_hypothesis
    on_failure: notify_failure

  # Step 5: Form hypothesis
  - id: formulate_hypothesis
    type: agent
    prompt_template: |
      Based on the analysis:
      {{context.step_outputs.analyze_patterns}}

      Formulate a root cause hypothesis:
      1. Most likely root cause
      2. Supporting evidence
      3. Alternative explanations
      4. Recommended remediation steps
      5. Risk assessment of remediation
    allowed_tools: []
    timeout_seconds: 300
    on_success: human_review_checkpoint
    on_failure: notify_failure

  # Step 6: Human review checkpoint
  - id: human_review_checkpoint
    type: checkpoint
    description: "SRE review of investigation findings"
    message: |
      ## Investigation Complete - Review Required

      **Pod**: {{context.findings.pod_name}}
      **Namespace**: {{context.findings.namespace}}

      **Root Cause Hypothesis**:
      {{context.step_outputs.formulate_hypothesis.root_cause}}

      **Proposed Remediation**:
      {{context.step_outputs.formulate_hypothesis.remediation}}

      **Risk Level**: {{context.step_outputs.formulate_hypothesis.risk_level}}

      Please review and approve to proceed with remediation.
    notification:
      slack:
        channel: "#sre-oncall"
        mention: "@sre-oncall"
      email:
        to: "sre@company.com"
    timeout_seconds: 3600  # 1 hour
    on_approve: apply_remediation
    on_reject: escalate_to_senior_sre
    on_timeout: escalate_to_senior_sre

  # Step 7: Apply remediation (if approved)
  - id: apply_remediation
    type: agent
    prompt_template: |
      Apply the approved remediation:
      {{context.step_outputs.formulate_hypothesis.remediation}}

      IMPORTANT: Execute commands carefully. Confirm before making changes.

      Remediation steps approved by: {{context.approvals.human_review_checkpoint.approved_by}}
    allowed_tools: ["Bash"]
    timeout_seconds: 600
    retry_policy:
      max_attempts: 1  # No retry for remediation
    on_success: verify_resolution
    on_failure: rollback_changes

  # Step 8: Verify resolution
  - id: verify_resolution
    type: agent
    prompt_template: |
      Verify that the issue is resolved:

      1. Check pod status: kubectl get pod {{context.findings.pod_name}} -n {{context.findings.namespace}}
      2. Check recent events
      3. Monitor logs for errors
      4. Check metrics (CPU, memory, restart count)

      Confirm:
      - Pod is running
      - No crash loops
      - No errors in logs
      - Application is healthy
    allowed_tools: ["Bash"]
    timeout_seconds: 300
    on_success: generate_rca_report
    on_failure: notify_verification_failed

  # Step 9: Generate RCA report
  - id: generate_rca_report
    type: agent
    prompt_template: |
      Generate a comprehensive RCA (Root Cause Analysis) report:

      ## Incident Summary
      - Incident ID: {{workflow_execution_id}}
      - Pod: {{context.findings.pod_name}}
      - Namespace: {{context.findings.namespace}}
      - Detected: {{workflow_started_at}}
      - Resolved: {{current_timestamp}}

      ## Timeline
      [Create timeline from all step outputs]

      ## Root Cause
      {{context.step_outputs.formulate_hypothesis.root_cause}}

      ## Evidence
      [Summarize key findings from logs and analysis]

      ## Remediation Applied
      {{context.step_outputs.apply_remediation}}

      ## Verification
      {{context.step_outputs.verify_resolution}}

      ## Prevention Measures
      [Suggest how to prevent recurrence]

      ## Lessons Learned
      [What we learned from this incident]
    allowed_tools: ["Write"]
    timeout_seconds: 300
    on_success: notify_completion
    on_failure: notify_completion  # Report even if RCA gen fails

  # Step 10: Notify completion
  - id: notify_completion
    type: webhook
    webhook_url: "{{config.completion_webhook}}"
    payload:
      status: "completed"
      workflow_execution_id: "{{workflow_execution_id}}"
      rca_report: "{{context.step_outputs.generate_rca_report}}"
      duration_seconds: "{{workflow_duration}}"

  # Error handling steps
  - id: escalate_to_senior_sre
    type: webhook
    description: "Escalate to senior SRE team"
    webhook_url: "{{config.pagerduty_webhook}}"
    payload:
      severity: "high"
      title: "Pod crash investigation requires senior SRE review"
      details: "{{context}}"

  - id: notify_failure
    type: webhook
    webhook_url: "{{config.alert_webhook}}"
    payload:
      status: "failed"
      workflow_execution_id: "{{workflow_execution_id}}"
      error: "{{error_message}}"

  - id: rollback_changes
    type: agent
    prompt_template: "Rollback changes made in apply_remediation step"
    allowed_tools: ["Bash"]
    on_success: notify_rollback_success
    on_failure: notify_rollback_failed
```

## Implementation Tasks

### Phase 1: Core Workflow Engine (Sprint 1-3)
1. **Create database schema** (workflow_definitions, workflow_executions, workflow_step_executions)
2. **Implement WorkflowDefinition domain entity** with validation
3. **Create WorkflowEngine service** for orchestration
4. **Implement step executor** for agent steps
5. **Create state machine** for workflow execution
6. **Implement workflow context** management

### Phase 2: Step Types (Sprint 4-5)
7. **Implement agent step executor** (integrate with SessionService)
8. **Implement checkpoint step executor** (human approval)
9. **Implement webhook step executor** (external calls)
10. **Implement script step executor** (custom logic)
11. **Add conditional branching** (if-else logic)
12. **Add parallel step execution** support

### Phase 3: Human Checkpoints & Notifications (Sprint 6)
13. **Create checkpoint approval API**
14. **Implement notification service** integration
15. **Add Slack notification** for checkpoints
16. **Add email notification** for checkpoints
17. **Implement approval timeout** handling
18. **Create approval dashboard** API

### Phase 4: Error Handling & Recovery (Sprint 7)
19. **Implement retry logic** for failed steps
20. **Add rollback mechanisms**
21. **Create pause/resume** functionality
22. **Implement workflow cancellation**
23. **Add step-level error handlers**

### Phase 5: Integration & Templates (Sprint 8)
24. **Integrate with event triggers** (US001)
25. **Create workflow templates** library (K8s, AWS, Azure)
26. **Add workflow versioning**
27. **Implement workflow import/export**
28. **Create workflow validation** service

## Success Metrics
- **Workflow completion rate**: > 90%
- **Average investigation time**: < 15 minutes for common issues
- **Human intervention required**: < 20% of workflows
- **Approval response time**: < 30 minutes median
- **RCA quality score**: > 4/5 (based on SRE feedback)

## Future Enhancements
- Visual workflow builder UI (drag-and-drop)
- Workflow templates marketplace
- AI-suggested workflow improvements based on execution history
- Integration with runbook automation platforms
- Workflow A/B testing for optimization

## Related Documentation
- `/docs/user-stories/US001-event-driven-triggers.md` - Event triggers
- `/docs/components/sessions/SESSION_LIFECYCLE.md` - Session management
- `/docs/components/tasks/TASK_AUTOMATION.md` - Task automation

---

**Created**: 2025-10-20
**Author**: AI Architecture Analysis
**Status**: PROPOSED
**Review Status**: Pending
