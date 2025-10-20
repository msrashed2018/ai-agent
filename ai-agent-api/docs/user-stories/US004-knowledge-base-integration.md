# US004: Knowledge Base & Runbook Integration

## Overview
**Epic**: Intelligent Knowledge Management
**Priority**: MEDIUM
**Complexity**: Medium
**Target Release**: v2.3

## User Story
**As a** team lead (DevOps/SRE/Support)
**I want** AI agents to access and learn from organizational knowledge bases, runbooks, and past incident reports
**So that** the agent can provide solutions based on company-specific procedures and historical resolutions

## Current State Analysis
The service currently supports:
- ✅ Session working directories with Read/Write tools
- ✅ MCP tool integration
- ✅ Task templates with prompt templates
- ❌ **MISSING**: Vector database for semantic search
- ❌ **MISSING**: Knowledge base document ingestion
- ❌ **MISSING**: Runbook execution tracking
- ❌ **MISSING**: Historical incident search
- ❌ **MISSING**: Solution recommendation based on past cases

## Problem Statement
Every organization has:
- **Runbooks**: Step-by-step procedures for common tasks
- **Incident Reports**: Post-mortems from past incidents
- **Documentation**: Internal wikis, README files, architecture docs
- **Tribal Knowledge**: Solutions shared in Slack, email, tickets

When investigating an issue, agents should be able to:
1. Search for similar past incidents
2. Find relevant runbooks automatically
3. Reference internal documentation
4. Apply company-specific best practices
5. Learn from historical resolutions

Currently, all this knowledge is external to the agent - it has no memory of past investigations or access to company procedures.

## Proposed Solution

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│              AI Agent (Claude Code)                      │
│  "Find similar incidents to this pod crash"            │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol
                       ▼
┌─────────────────────────────────────────────────────────┐
│      Knowledge Base MCP Server (New Component)          │
│  ┌───────────────────────────────────────────────────┐ │
│  │  MCP Tools:                                       │ │
│  │  • search_knowledge(query, filters)              │ │
│  │  • get_runbook(id or topic)                      │ │
│  │  • find_similar_incidents(description)           │ │
│  │  • get_solution(problem_signature)               │ │
│  │  • execute_runbook_step(runbook_id, step_num)    │ │
│  │  • save_learning(incident_id, solution)          │ │
│  └───────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┬──────────────┐
       ▼               ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Vector  │   │Document  │   │ Runbook  │   │Incident  │
│    DB    │   │ Ingestion│   │ Executor │   │  Index   │
│(ChromaDB)│   │ Pipeline │   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## Acceptance Criteria

### Knowledge Ingestion
- [ ] **AC1**: System can ingest Markdown, PDF, HTML documents
- [ ] **AC2**: System extracts and indexes runbooks (structured procedures)
- [ ] **AC3**: Completed investigations are automatically saved as knowledge
- [ ] **AC4**: System supports versioning of runbooks and docs
- [ ] **AC5**: Users can manually add/edit knowledge entries

### Semantic Search
- [ ] **AC6**: Agent can search knowledge base using natural language
- [ ] **AC7**: Search results ranked by relevance (vector similarity)
- [ ] **AC8**: Search supports filtering (by category, date, severity, tags)
- [ ] **AC9**: Search includes snippets highlighting relevant sections
- [ ] **AC10**: Agent can retrieve full documents when needed

### Runbook Management
- [ ] **AC11**: Runbooks are structured with steps, conditions, and decisions
- [ ] **AC12**: Agent can execute runbook steps sequentially
- [ ] **AC13**: Runbook execution tracks completion and outcomes
- [ ] **AC14**: Failed runbook steps are logged with context
- [ ] **AC15**: Runbooks support conditional branching (if-then logic)

### Incident Similarity
- [ ] **AC16**: System finds similar past incidents using vector similarity
- [ ] **AC17**: Similarity matching considers: symptoms, services, errors, resolution
- [ ] **AC18**: Results show: similarity score, resolution time, solution applied
- [ ] **AC19**: Agent can learn from how similar incidents were resolved
- [ ] **AC20**: Users can mark incidents as similar/not similar (feedback loop)

### Learning & Improvement
- [ ] **AC21**: Successful investigations are auto-saved as new knowledge
- [ ] **AC22**: Solutions are linked to problem signatures
- [ ] **AC23**: System tracks which solutions work for which problems
- [ ] **AC24**: Popular/effective solutions are ranked higher
- [ ] **AC25**: Knowledge base is searchable by UI and API

## Database Schema Changes

### New Table: `knowledge_documents`
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),          -- NULL for shared docs
    organization_id UUID NOT NULL,

    -- Document metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    document_type VARCHAR(50),                   -- 'runbook', 'incident_report', 'documentation', 'wiki', 'solution'
    category VARCHAR(100),                       -- 'kubernetes', 'database', 'networking', etc.
    tags JSONB,

    -- Content
    content_text TEXT NOT NULL,                  -- Full text content
    content_markdown TEXT,                       -- Original markdown if applicable
    content_structured JSONB,                    -- Structured data (for runbooks)

    -- Vector embeddings (for semantic search)
    embedding vector(1536),                      -- Using pgvector extension

    -- Source
    source_type VARCHAR(50),                     -- 'manual', 'investigation', 'import', 'github'
    source_url TEXT,
    source_file_path TEXT,

    -- Versioning
    version INT DEFAULT 1,
    parent_document_id UUID REFERENCES knowledge_documents(id),

    -- Access control
    is_public BOOLEAN DEFAULT false,
    allowed_teams JSONB,

    -- Metrics
    view_count INT DEFAULT 0,
    usefulness_score DECIMAL(3,2) DEFAULT 0.0,   -- Based on user feedback
    last_used_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    INDEX idx_knowledge_documents_document_type (document_type),
    INDEX idx_knowledge_documents_category (category),
    INDEX idx_knowledge_documents_embedding vector_cosine_ops (embedding),  -- For pgvector
    INDEX idx_knowledge_documents_tags (tags) USING GIN
);
```

### New Table: `runbooks`
```sql
CREATE TABLE runbooks (
    id UUID PRIMARY KEY,
    knowledge_document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,

    -- Runbook metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags JSONB,

    -- Trigger conditions
    trigger_patterns JSONB,                     -- When to suggest this runbook
    /*
    Example:
    {
      "symptoms": ["pod crash", "OOMKilled", "high memory"],
      "services": ["web-app", "api-gateway"],
      "error_patterns": ["OutOfMemoryError"]
    }
    */

    -- Runbook steps
    steps JSONB NOT NULL,
    /*
    Example:
    [
      {
        "step_number": 1,
        "title": "Check pod status",
        "description": "Get current status of the affected pod",
        "action_type": "bash_command",  // or "agent_prompt", "manual", "conditional"
        "action": "kubectl get pod {{pod_name}} -n {{namespace}}",
        "expected_output": "...",
        "on_success": 2,
        "on_failure": 10  // Jump to troubleshooting step
      },
      {
        "step_number": 2,
        "title": "Analyze logs",
        "action_type": "agent_prompt",
        "action": "Analyze the pod logs and identify error patterns",
        ...
      }
    ]
    */

    -- Execution stats
    execution_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    avg_execution_time_ms BIGINT,
    last_executed_at TIMESTAMP,

    -- Effectiveness
    effectiveness_score DECIMAL(3,2),            -- Success rate and user feedback

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_runbooks_category (category),
    INDEX idx_runbooks_tags (tags) USING GIN
);
```

### New Table: `runbook_executions`
```sql
CREATE TABLE runbook_executions (
    id UUID PRIMARY KEY,
    runbook_id UUID NOT NULL REFERENCES runbooks(id),
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    session_id UUID REFERENCES sessions(id),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Context
    execution_context JSONB,                     -- Variables, incident details

    -- Progress
    status VARCHAR(50) NOT NULL,                 -- 'in_progress', 'completed', 'failed', 'abandoned'
    current_step_number INT,
    completed_steps JSONB,                       -- Array of completed step numbers
    failed_steps JSONB,

    -- Results
    outcome VARCHAR(50),                         -- 'resolved', 'partially_resolved', 'escalated', 'failed'
    resolution_notes TEXT,
    effectiveness_rating INT,                    -- 1-5 stars (user feedback)

    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms BIGINT,

    INDEX idx_runbook_executions_runbook_id (runbook_id),
    INDEX idx_runbook_executions_status (status)
);
```

### New Table: `incident_knowledge`
```sql
CREATE TABLE incident_knowledge (
    id UUID PRIMARY KEY,
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    session_id UUID REFERENCES sessions(id),
    knowledge_document_id UUID REFERENCES knowledge_documents(id),
    organization_id UUID NOT NULL,

    -- Incident details
    incident_title VARCHAR(500),
    incident_type VARCHAR(100),                  -- 'outage', 'degradation', 'error', 'anomaly'
    severity VARCHAR(50),                        -- 'critical', 'high', 'medium', 'low'

    -- Problem signature (for similarity matching)
    problem_signature JSONB,
    /*
    {
      "symptoms": ["high CPU", "pod crash"],
      "error_messages": ["OutOfMemoryError"],
      "affected_services": ["web-app"],
      "infrastructure": "kubernetes"
    }
    */
    problem_embedding vector(1536),

    -- Solution
    root_cause TEXT,
    solution_applied TEXT,
    resolution_steps JSONB,

    -- Metadata
    tags JSONB,
    related_incidents UUID[],                    -- Similar incident IDs

    -- Effectiveness
    resolution_time_minutes INT,
    was_successful BOOLEAN,
    recurred BOOLEAN DEFAULT false,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_incident_knowledge_incident_type (incident_type),
    INDEX idx_incident_knowledge_severity (severity),
    INDEX idx_incident_knowledge_problem_embedding vector_cosine_ops (problem_embedding)
);
```

### New Table: `knowledge_feedback`
```sql
CREATE TABLE knowledge_feedback (
    id UUID PRIMARY KEY,
    knowledge_document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),

    -- Feedback
    feedback_type VARCHAR(50),                   -- 'helpful', 'not_helpful', 'outdated', 'incorrect'
    rating INT,                                  -- 1-5 stars
    comment TEXT,

    -- Context
    search_query TEXT,                           -- What they were looking for
    was_used BOOLEAN DEFAULT false,              -- Did they use this knowledge?

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_knowledge_feedback_knowledge_document_id (knowledge_document_id),
    INDEX idx_knowledge_feedback_feedback_type (feedback_type)
);
```

## MCP Tools Specification

### Tool: `search_knowledge`
```typescript
{
  name: "search_knowledge",
  description: "Search organizational knowledge base using semantic search",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query in natural language"
      },
      filters: {
        type: "object",
        properties: {
          document_type: {
            type: "array",
            items: { type: "string" }
          },
          category: { type: "string" },
          tags: { type: "array" },
          min_usefulness_score: { type: "number" }
        }
      },
      limit: { type: "number", default: 10 }
    }
  }
}

Response:
{
  "results": [
    {
      "id": "uuid",
      "title": "Resolving Pod OOMKilled Issues",
      "document_type": "solution",
      "category": "kubernetes",
      "relevance_score": 0.92,
      "snippet": "...memory limits should be set to 2Gi for production pods...",
      "last_used": "2025-10-15T14:30:00Z",
      "usefulness_score": 4.5,
      "url": "/knowledge/uuid"
    }
  ]
}
```

### Tool: `get_runbook`
```typescript
{
  name: "get_runbook",
  description: "Get a specific runbook or find runbook by topic/problem",
  inputSchema: {
    type: "object",
    properties: {
      runbook_id: { type: "string" },
      topic: { type: "string" },
      problem_description: { type: "string" }
    }
  }
}

Response:
{
  "id": "uuid",
  "name": "Pod Crash Investigation Runbook",
  "description": "Standard procedure for investigating pod crashes",
  "steps": [
    {
      "step_number": 1,
      "title": "Identify crashed pod",
      "action_type": "bash_command",
      "action": "kubectl get pods -n {{namespace}} | grep -v Running",
      "expected_output": "List of non-running pods"
    },
    ...
  ],
  "execution_count": 45,
  "success_rate": 0.87,
  "avg_execution_time_minutes": 12
}
```

### Tool: `find_similar_incidents`
```typescript
{
  name: "find_similar_incidents",
  description: "Find past incidents similar to current problem",
  inputSchema: {
    type: "object",
    properties: {
      description: {
        type: "string",
        description: "Description of current problem"
      },
      symptoms: {
        type: "array",
        items: { type: "string" }
      },
      affected_services: {
        type: "array",
        items: { type: "string" }
      },
      limit: { type: "number", default: 5 }
    }
  }
}

Response:
{
  "similar_incidents": [
    {
      "id": "uuid",
      "title": "Production Web App OOMKilled - Oct 15",
      "similarity_score": 0.89,
      "severity": "high",
      "root_cause": "Memory leak in version 2.5",
      "solution": "Rolled back to version 2.4, increased memory limits",
      "resolution_time_minutes": 25,
      "occurred_at": "2025-10-15T10:30:00Z",
      "matching_symptoms": ["pod crash", "OOMKilled", "high memory"]
    }
  ]
}
```

### Tool: `save_learning`
```typescript
{
  name: "save_learning",
  description: "Save investigation findings as new knowledge",
  inputSchema: {
    type: "object",
    properties: {
      title: { type: "string" },
      document_type: {
        type: "string",
        enum: ["incident_report", "solution", "runbook"]
      },
      content: { type: "string" },
      problem_signature: {
        type: "object",
        properties: {
          symptoms: { type: "array" },
          error_messages: { type: "array" },
          affected_services: { type: "array" }
        }
      },
      solution: { type: "string" },
      tags: { type: "array" },
      related_incident_ids: { type: "array" }
    }
  }
}
```

## Implementation Tasks

### Phase 1: Infrastructure (Sprint 1-2)
1. **Set up Vector Database** (pgvector extension or ChromaDB)
2. **Create database schema** (knowledge_documents, runbooks, etc.)
3. **Implement embedding generation** (using OpenAI or local model)
4. **Create KnowledgeDocument entity** and repository
5. **Create Runbook entity** and repository
6. **Set up document ingestion pipeline**

### Phase 2: Knowledge Management (Sprint 3-4)
7. **Implement semantic search** using vector similarity
8. **Create knowledge CRUD APIs**
9. **Build document parser** (Markdown, PDF, HTML)
10. **Implement versioning** for documents
11. **Add tagging and categorization**
12. **Create feedback collection** system

### Phase 3: Runbook Engine (Sprint 5-6)
13. **Implement runbook parser** (YAML/JSON format)
14. **Create RunbookExecutor** service
15. **Build step execution** logic (bash, agent prompts)
16. **Implement conditional branching**
17. **Add execution tracking** and metrics
18. **Create runbook recommendation** engine

### Phase 4: Incident Learning (Sprint 7-8)
19. **Implement automatic knowledge extraction** from investigations
20. **Create incident similarity** matching (vector-based)
21. **Build problem signature** generation
22. **Implement solution recommendation** based on past cases
23. **Add feedback loop** for learning effectiveness
24. **Create knowledge quality** scoring

### Phase 5: MCP Server (Sprint 9)
25. **Implement MCP tools** (search_knowledge, get_runbook, etc.)
26. **Create MCP server** for knowledge base
27. **Add caching layer** for frequent queries
28. **Implement access control** for knowledge
29. **Deploy MCP server** with configuration
30. **Create user documentation**

## Example Runbook Format

### YAML Runbook Definition
```yaml
name: "Kubernetes Pod Crash Investigation"
version: 1.0
category: kubernetes
tags: [pods, crashes, debugging]

trigger_patterns:
  symptoms:
    - pod crash
    - crashloopbackoff
    - OOMKilled
  error_patterns:
    - "Exit Code 1"
    - "Exit Code 137"

variables:
  namespace: production
  max_log_lines: 500

steps:
  - step: 1
    title: "Identify crashed pod details"
    action_type: bash
    command: |
      kubectl get pod {{pod_name}} -n {{namespace}} -o yaml
    extract:
      exit_code: ".status.containerStatuses[0].lastState.terminated.exitCode"
      restart_count: ".status.containerStatuses[0].restartCount"
    on_success: 2
    on_failure: abort

  - step: 2
    title: "Get pod logs from previous run"
    action_type: bash
    command: |
      kubectl logs {{pod_name}} -n {{namespace}} --previous --tail={{max_log_lines}}
    on_success: 3
    on_failure: 3  # Continue even if logs unavailable

  - step: 3
    title: "Analyze logs for error patterns"
    action_type: agent_prompt
    prompt: |
      Analyze these logs and identify:
      1. Error messages or exceptions
      2. Timing of errors
      3. Potential root causes

      Logs:
      {{step_2_output}}
    on_success: 4

  - step: 4
    title: "Check resource limits"
    action_type: conditional
    condition: "{{exit_code}} == 137"  # OOMKilled
    if_true: 5
    if_false: 6

  - step: 5
    title: "Analyze memory usage"
    action_type: agent_prompt
    prompt: |
      The pod was OOMKilled (exit code 137).
      Check:
      1. Memory limits in pod spec
      2. Historical memory usage
      3. Recent code changes
      4. Memory leak indicators

      Recommend whether to:
      - Increase memory limits
      - Fix memory leak
      - Optimize application
    on_success: 10

  - step: 6
    title: "Check for application errors"
    action_type: bash
    command: |
      kubectl describe pod {{pod_name}} -n {{namespace}}
    on_success: 7

  - step: 7
    title: "Get recent events"
    action_type: bash
    command: |
      kubectl get events -n {{namespace}} \
        --field-selector involvedObject.name={{pod_name}} \
        --sort-by='.lastTimestamp'
    on_success: 10

  - step: 10
    title: "Formulate root cause and solution"
    action_type: agent_prompt
    prompt: |
      Based on all gathered information:
      {{all_previous_outputs}}

      Provide:
      1. Root cause
      2. Recommended solution
      3. Prevention measures
    final_step: true
```

## Success Metrics
- **Search relevance**: > 80% of top-3 results rated helpful
- **Runbook success rate**: > 85% completion rate
- **Knowledge reuse**: > 50% of investigations use existing knowledge
- **Time saved**: 30% reduction in investigation time
- **Knowledge growth**: 10+ new documents per week

## Future Enhancements
- AI-generated runbooks from successful investigations
- Automatic knowledge base updates from Slack/Confluence
- Multi-language support for international teams
- Integration with ITSM platforms (ServiceNow, Jira)
- Knowledge graph visualization

---

**Created**: 2025-10-20
**Author**: AI Architecture Analysis
**Status**: PROPOSED
**Review Status**: Pending
