# Frontend API Updates Required - Phase 1-5 Integration

**Status**: 🔴 Action Required
**Priority**: P1 - Required for Full Feature Support
**Created**: 2025-10-19
**Version**: 1.0

---

## Executive Summary

Based on the Claude Agent SDK Phase 1-5 implementation in `ai-agent-api`, the frontend requires updates to support new features:

- **7 New API Endpoints** for sessions (fork, archive, hooks, permissions, metrics)
- **6 New Response Types** added to schemas
- **9 New Fields** in SessionCreateRequest
- **2 New Fields** in SessionResponse

**Estimated Implementation Time**: 6-8 hours
**Complexity**: Medium (mostly additive changes)

---

## 📋 Required Changes Summary

### 1. Type Definitions (`src/types/api.ts`)
- Add Phase 4 fields to `SessionCreateRequest`
- Add Phase 4 fields to `SessionResponse`
- Add 6 new response types

### 2. API Client (`src/lib/api-client.ts`)
- Add 7 new session endpoints
- Add 8 new monitoring endpoints (optional)

### 3. Session Hooks (`src/hooks/use-sessions.ts`)
- Add hooks for new session operations

### 4. UI Components (Optional - Progressive)
- Session fork UI
- Archive management UI
- Hooks/permissions viewer
- Metrics dashboard

---

## 🔧 Detailed Changes Required

### Part 1: Update Type Definitions

**File**: `src/types/api.ts`

#### 1.1 Update SessionCreateRequest

**Current** (lines 40-48):
```typescript
export interface SessionCreateRequest {
  name?: string | null;
  description?: string | null;
  model?: string;
  allowed_tools?: string[];
  system_prompt?: string | null;
  mcp_servers?: string[];
  parent_session_id?: string | null;
}
```

**Updated** (add Phase 4 fields):
```typescript
export interface SessionCreateRequest {
  // Existing fields
  template_id?: string | null;
  name?: string | null;
  description?: string | null;
  working_directory?: string | null;
  allowed_tools?: string[];
  system_prompt?: string | null;
  sdk_options?: Record<string, any> | null;
  metadata?: Record<string, any> | null;

  // Phase 4: Session mode
  mode?: 'interactive' | 'background' | 'forked';

  // Phase 4: Parent session (for forking)
  parent_session_id?: string | null;
  fork_at_message?: number | null;

  // Phase 4: Streaming configuration
  include_partial_messages?: boolean;

  // Phase 4: Retry configuration
  max_retries?: number;
  retry_delay?: number;
  timeout_seconds?: number;

  // Phase 4: Hooks configuration
  hooks_enabled?: string[];

  // Phase 4: Permission configuration
  permission_mode?: 'default' | 'acceptEdits' | 'bypassPermissions';
  custom_policies?: string[];
}
```

#### 1.2 Update SessionResponse

**Add these fields** to SessionResponse (after line 67):
```typescript
export interface SessionResponse {
  // ... existing fields ...

  // Phase 4: Additional fields
  mode?: string;
  is_fork: boolean;
  fork_at_message?: number | null;
  include_partial_messages?: boolean;
  max_retries?: number;
  retry_delay?: number;
  timeout_seconds?: number;
  hooks_enabled?: string[];
  permission_mode?: string;
  custom_policies?: string[];
  total_hook_executions?: number;
  total_permission_checks?: number;
  total_errors?: number;
  total_retries?: number;
  archive_id?: string | null;
  template_id?: string | null;
  total_input_tokens?: number;
  total_output_tokens?: number;
  total_cache_creation_tokens?: number;
  total_cache_read_tokens?: number;
}
```

#### 1.3 Add New Response Types

**Add after ReportListResponse** (around line 273):

```typescript
// ============================================================================
// Phase 4: Advanced Session Features
// ============================================================================

export interface SessionForkRequest {
  name?: string | null;
  fork_at_message?: number | null;
  include_working_directory?: boolean;
}

export interface SessionArchiveRequest {
  upload_to_s3?: boolean;
  compression?: string;
}

export interface HookExecutionResponse {
  id: string;
  session_id: string;
  hook_type: string;
  hook_name: string;
  tool_use_id?: string | null;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  continue_execution: boolean;
  executed_at: string;
  duration_ms?: number | null;
}

export interface PermissionDecisionResponse {
  id: string;
  session_id: string;
  tool_name: string;
  input_data: Record<string, any>;
  context: Record<string, any>;
  decision: 'allow' | 'deny';
  reason?: string | null;
  interrupted: boolean;
  decided_at: string;
}

export interface ArchiveMetadataResponse {
  id: string;
  session_id: string;
  archive_path: string;
  size_bytes: number;
  compression: string;
  manifest: Record<string, any>;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  error_message?: string | null;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MetricsSnapshotResponse {
  id: string;
  session_id: string;
  total_messages: number;
  total_tool_calls: number;
  total_errors: number;
  total_retries: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cache_creation_tokens: number;
  total_cache_read_tokens: number;
  total_duration_ms: number;
  created_at: string;
}

export interface SessionMetricsResponse {
  session_id: string;
  current_metrics: MetricsSnapshotResponse;
  previous_snapshots: MetricsSnapshotResponse[];
  performance_trends: {
    messages_per_hour: number;
    average_cost_per_message: number;
    error_rate_percent: number;
    cache_hit_rate_percent: number;
  };
}

// ============================================================================
// Phase 4: Monitoring
// ============================================================================

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  components: Record<string, {
    status: 'healthy' | 'unhealthy' | 'unknown';
    message?: string;
    timestamp: string;
  }>;
  timestamp: string;
}

export interface CostSummaryResponse {
  user_id: string;
  period: 'today' | 'week' | 'month';
  total_cost_usd: number;
  session_count: number;
  message_count: number;
  average_cost_per_session: number;
  start_date: string;
  end_date: string;
  breakdown_by_model: Record<string, number>;
}
```

#### 1.4 Add Utility Types

**Add at the end** (after line 435):
```typescript
export type SessionMode = 'interactive' | 'background' | 'forked';
export type PermissionMode = 'default' | 'acceptEdits' | 'bypassPermissions';
export type ArchiveStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
export type PermissionDecision = 'allow' | 'deny';
export type HookType = 'PreToolUse' | 'PostToolUse' | 'UserPromptSubmit' | 'Stop' | 'SubagentStop' | 'PreCompact';
```

---

### Part 2: Update API Client

**File**: `src/lib/api-client.ts`

#### 2.1 Update Imports

**Add to imports** (after line 37):
```typescript
import type {
  // ... existing imports ...
  SessionForkRequest,
  SessionArchiveRequest,
  HookExecutionResponse,
  PermissionDecisionResponse,
  ArchiveMetadataResponse,
  MetricsSnapshotResponse,
  SessionMetricsResponse,
  HealthCheckResponse,
  CostSummaryResponse,
} from '@/types/api';
```

#### 2.2 Add Session Fork Endpoint

**Add after downloadWorkdir** (after line 211):
```typescript
  // ============================================================================
  // Phase 4: Advanced Session Features
  // ============================================================================

  async forkSession(sessionId: string, data: SessionForkRequest): Promise<SessionResponse> {
    const response = await this.client.post<SessionResponse>(
      `/api/v1/sessions/${sessionId}/fork`,
      data
    );
    return response.data;
  }

  async archiveSession(sessionId: string, data: SessionArchiveRequest): Promise<ArchiveMetadataResponse> {
    const response = await this.client.post<ArchiveMetadataResponse>(
      `/api/v1/sessions/${sessionId}/archive`,
      data
    );
    return response.data;
  }

  async getSessionArchive(sessionId: string): Promise<ArchiveMetadataResponse> {
    const response = await this.client.get<ArchiveMetadataResponse>(
      `/api/v1/sessions/${sessionId}/archive`
    );
    return response.data;
  }

  async getSessionHooks(sessionId: string, limit: number = 50): Promise<HookExecutionResponse[]> {
    const response = await this.client.get<HookExecutionResponse[]>(
      `/api/v1/sessions/${sessionId}/hooks`,
      { params: { limit } }
    );
    return response.data;
  }

  async getSessionPermissions(sessionId: string, limit: number = 50): Promise<PermissionDecisionResponse[]> {
    const response = await this.client.get<PermissionDecisionResponse[]>(
      `/api/v1/sessions/${sessionId}/permissions`,
      { params: { limit } }
    );
    return response.data;
  }

  async getSessionMetricsSnapshots(sessionId: string, limit: number = 50): Promise<MetricsSnapshotResponse[]> {
    const response = await this.client.get<MetricsSnapshotResponse[]>(
      `/api/v1/sessions/${sessionId}/metrics/snapshots`,
      { params: { limit } }
    );
    return response.data;
  }

  async getCurrentSessionMetrics(sessionId: string): Promise<SessionMetricsResponse> {
    const response = await this.client.get<SessionMetricsResponse>(
      `/api/v1/sessions/${sessionId}/metrics/current`
    );
    return response.data;
  }
```

#### 2.3 Add Monitoring Endpoints (Optional)

**Add after session templates** (after line 408):
```typescript
  // ============================================================================
  // Phase 4: Monitoring (Optional)
  // ============================================================================

  async getSystemHealth(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/v1/monitoring/health');
    return response.data;
  }

  async getDatabaseHealth(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/v1/monitoring/health/database');
    return response.data;
  }

  async getSDKHealth(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/v1/monitoring/health/sdk');
    return response.data;
  }

  async getUserCosts(period: 'today' | 'week' | 'month' = 'today'): Promise<CostSummaryResponse> {
    const response = await this.client.get<CostSummaryResponse>(
      '/api/v1/monitoring/costs/user',
      { params: { period } }
    );
    return response.data;
  }

  async getUserBudgetStatus(): Promise<any> {
    const response = await this.client.get('/api/v1/monitoring/costs/user/budget');
    return response.data;
  }

  async getSessionMetrics(sessionId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/monitoring/sessions/${sessionId}/metrics`);
    return response.data;
  }
```

---

### Part 3: Update Session Hooks

**File**: `src/hooks/use-sessions.ts`

#### 3.1 Add to Existing Hook

**Find the `useSessions` hook and add** these mutations:

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import type {
  SessionForkRequest,
  SessionArchiveRequest,
  HookExecutionResponse,
  PermissionDecisionResponse,
  MetricsSnapshotResponse,
  SessionMetricsResponse,
} from '@/types/api';

// ... existing code ...

// Add these new hooks:

export function useSessionFork() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: SessionForkRequest }) =>
      apiClient.forkSession(sessionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

export function useSessionArchive() {
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: SessionArchiveRequest }) =>
      apiClient.archiveSession(sessionId, data),
  });
}

export function useSessionHooks(sessionId: string, limit: number = 50) {
  return useQuery<HookExecutionResponse[]>({
    queryKey: ['session-hooks', sessionId, limit],
    queryFn: () => apiClient.getSessionHooks(sessionId, limit),
    enabled: !!sessionId,
  });
}

export function useSessionPermissions(sessionId: string, limit: number = 50) {
  return useQuery<PermissionDecisionResponse[]>({
    queryKey: ['session-permissions', sessionId, limit],
    queryFn: () => apiClient.getSessionPermissions(sessionId, limit),
    enabled: !!sessionId,
  });
}

export function useSessionMetrics(sessionId: string) {
  return useQuery<SessionMetricsResponse>({
    queryKey: ['session-metrics', sessionId],
    queryFn: () => apiClient.getCurrentSessionMetrics(sessionId),
    enabled: !!sessionId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useSessionMetricsSnapshots(sessionId: string, limit: number = 50) {
  return useQuery<MetricsSnapshotResponse[]>({
    queryKey: ['session-metrics-snapshots', sessionId, limit],
    queryFn: () => apiClient.getSessionMetricsSnapshots(sessionId, limit),
    enabled: !!sessionId,
  });
}
```

---

### Part 4: UI Components (Optional - Progressive Implementation)

These components are **optional** but recommended for full feature support:

#### 4.1 Session Fork Dialog

**Create**: `src/components/sessions/fork-session-dialog.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useSessionFork } from '@/hooks/use-sessions';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

interface ForkSessionDialogProps {
  sessionId: string;
  onSuccess?: () => void;
}

export function ForkSessionDialog({ sessionId, onSuccess }: ForkSessionDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [includeWorkdir, setIncludeWorkdir] = useState(true);
  const forkMutation = useSessionFork();

  const handleFork = async () => {
    try {
      await forkMutation.mutateAsync({
        sessionId,
        data: {
          name: name || null,
          include_working_directory: includeWorkdir,
        },
      });
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      console.error('Fork error:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Fork Session</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Fork Session</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="fork-name">Session Name (Optional)</Label>
            <Input
              id="fork-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Forked Session"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="include-workdir"
              checked={includeWorkdir}
              onCheckedChange={setIncludeWorkdir}
            />
            <Label htmlFor="include-workdir">Include Working Directory Files</Label>
          </div>
          <Button onClick={handleFork} disabled={forkMutation.isPending} className="w-full">
            {forkMutation.isPending ? 'Forking...' : 'Fork Session'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

#### 4.2 Session Metrics Panel

**Create**: `src/components/sessions/session-metrics-panel.tsx`

```typescript
'use client';

import { useSessionMetrics } from '@/hooks/use-sessions';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface SessionMetricsPanelProps {
  sessionId: string;
}

export function SessionMetricsPanel({ sessionId }: SessionMetricsPanelProps) {
  const { data: metrics, isLoading } = useSessionMetrics(sessionId);

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  if (!metrics) {
    return null;
  }

  const { current_metrics, performance_trends } = metrics;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Session Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Messages" value={current_metrics.total_messages} />
        <MetricCard label="Tool Calls" value={current_metrics.total_tool_calls} />
        <MetricCard label="Cost" value={`$${current_metrics.total_cost_usd.toFixed(4)}`} />
        <MetricCard label="Errors" value={current_metrics.total_errors} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <MetricCard
          label="Cache Hit Rate"
          value={`${performance_trends.cache_hit_rate_percent.toFixed(1)}%`}
        />
        <MetricCard
          label="Error Rate"
          value={`${performance_trends.error_rate_percent.toFixed(1)}%`}
        />
      </div>
    </Card>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
```

#### 4.3 Hooks & Permissions Viewer

**Create**: `src/components/sessions/hooks-permissions-viewer.tsx`

```typescript
'use client';

import { useSessionHooks, useSessionPermissions } from '@/hooks/use-sessions';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

interface HooksPermissionsViewerProps {
  sessionId: string;
}

export function HooksPermissionsViewer({ sessionId }: HooksPermissionsViewerProps) {
  const { data: hooks, isLoading: hooksLoading } = useSessionHooks(sessionId);
  const { data: permissions, isLoading: permissionsLoading } = useSessionPermissions(sessionId);

  return (
    <Card className="p-6">
      <Tabs defaultValue="hooks">
        <TabsList>
          <TabsTrigger value="hooks">Hooks ({hooks?.length || 0})</TabsTrigger>
          <TabsTrigger value="permissions">Permissions ({permissions?.length || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="hooks" className="space-y-2">
          {hooksLoading ? (
            <p>Loading hooks...</p>
          ) : hooks && hooks.length > 0 ? (
            hooks.map((hook) => (
              <div key={hook.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <Badge variant="outline">{hook.hook_type}</Badge>
                    <p className="font-medium mt-1">{hook.hook_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(hook.executed_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={hook.continue_execution ? 'default' : 'destructive'}>
                    {hook.continue_execution ? 'Continued' : 'Blocked'}
                  </Badge>
                </div>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No hooks executed yet</p>
          )}
        </TabsContent>

        <TabsContent value="permissions" className="space-y-2">
          {permissionsLoading ? (
            <p>Loading permissions...</p>
          ) : permissions && permissions.length > 0 ? (
            permissions.map((perm) => (
              <div key={perm.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{perm.tool_name}</p>
                    {perm.reason && (
                      <p className="text-xs text-muted-foreground mt-1">{perm.reason}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {new Date(perm.decided_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={perm.decision === 'allow' ? 'default' : 'destructive'}>
                    {perm.decision}
                  </Badge>
                </div>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No permission decisions yet</p>
          )}
        </TabsContent>
      </Tabs>
    </Card>
  );
}
```

---

## 📊 Implementation Priority

### P0 - Critical (Required for Basic Functionality)
- [ ] Update `SessionCreateRequest` type with Phase 4 fields
- [ ] Update `SessionResponse` type with Phase 4 fields
- [ ] Add new response types to `api.ts`

### P1 - High (Required for Advanced Features)
- [ ] Add session fork endpoint to API client
- [ ] Add session archive endpoint to API client
- [ ] Add session metrics endpoint to API client
- [ ] Add `useSessionFork` hook
- [ ] Add `useSessionMetrics` hook

### P2 - Medium (Nice to Have)
- [ ] Add hooks/permissions endpoints to API client
- [ ] Add `useSessionHooks` and `useSessionPermissions` hooks
- [ ] Create Fork Session Dialog component
- [ ] Create Session Metrics Panel component

### P3 - Low (Optional Enhancements)
- [ ] Add monitoring endpoints to API client
- [ ] Create Hooks & Permissions Viewer component
- [ ] Add archive management UI
- [ ] Add session mode selector in create dialog

---

## 🧪 Testing Checklist

After implementation, verify:

- [ ] TypeScript compilation succeeds without errors
- [ ] Session creation with new fields works
- [ ] Session fork creates a new session correctly
- [ ] Session metrics display properly
- [ ] Archive creation returns archive metadata
- [ ] Hooks and permissions data loads correctly
- [ ] All existing session features still work

---

## 📝 Breaking Changes

**None** - All changes are additive. Existing frontend code will continue to work without modification.

---

## 💡 Recommendations

1. **Start with Type Definitions**: Update `api.ts` first to ensure type safety
2. **API Client Next**: Add endpoints incrementally, test each one
3. **Hooks Layer**: Add React hooks for state management
4. **UI Components**: Build components progressively as needed
5. **Testing**: Test each layer before moving to the next

---

## 📚 References

- **API Schema**: `ai-agent-api/app/schemas/session.py`
- **API Endpoints**: `ai-agent-api/app/api/v1/sessions.py`
- **Phase Documentation**: `ai-agent-api/docs/phases/PHASE_4_API_AND_PRODUCTION.md`

---

## ⏱️ Estimated Timeline

- **Type Definitions**: 1 hour
- **API Client Updates**: 2 hours
- **React Hooks**: 1 hour
- **Basic UI Components**: 2-3 hours
- **Testing & QA**: 1-2 hours

**Total**: 6-8 hours for complete implementation

---

**Last Updated**: 2025-10-19
**Next Review**: After frontend implementation
