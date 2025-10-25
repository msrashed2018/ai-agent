// API Type Definitions - Generated from OpenAPI Schema

// ============================================================================
// Authentication Types
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  created_at: string;
}

// ===== Tool Call Types for Task Executions =====

export interface ToolCallResponse {
  id: string;
  session_id?: string | null;
  message_id?: string | null;
  tool_name: string;
  tool_use_id: string;
  tool_input: Record<string, any>;
  tool_output?: Record<string, any> | null;
  status: 'pending' | 'running' | 'success' | 'error' | 'denied';
  is_error: boolean;
  error_message?: string | null;
  permission_decision?: 'allow' | 'deny' | 'ask' | null;
  permission_reason?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  created_at: string;
  _links?: Links;
}

export interface ToolCallListResponse {
  items: ToolCallResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ===== NEW: Execution Cancellation Types =====

export interface ExecutionCancelRequest {
  reason?: string | null;
}

// ===== NEW: Working Directory Types =====

export interface WorkingDirectoryFileInfo {
  path: string;
  size: number;
  modified_at: string;
}

export interface WorkingDirectoryManifest {
  execution_id: string;
  total_files: number;
  total_size: number;
  files: WorkingDirectoryFileInfo[];
  _links?: Links;
}

export interface ArchiveResponse {
  execution_id: string;
  archive_path: string;
  archive_size: number;
  created_at: string;
  _links?: Links;
}

// ============================================================================
// Message & Tool Call Types
// ============================================================================

export interface MessageResponse {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

// ============================================================================
// Task Types
// ============================================================================

// ============================================================================
// Tool Group Types
// ============================================================================

export interface ToolGroupCreateRequest {
  name: string;
  description?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
}

export interface ToolGroupUpdateRequest {
  name?: string;
  description?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
}

export interface ToolGroupResponse {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  allowed_tools: string[];
  disallowed_tools: string[];
  is_public: boolean;
  is_active: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  _links?: Links;
}

export interface ToolGroupListResponse {
  items: ToolGroupResponse[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

// ============================================================================
// Task Types
// ============================================================================

export interface TaskCreateRequest {
  name: string;
  description?: string | null;
  prompt_template: string;
  template_variables?: Record<string, any>;
  tool_group_id?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  is_scheduled?: boolean;
  schedule_cron?: string | null;
  schedule_enabled?: boolean;
  generate_report?: boolean;
  report_format?: 'html' | 'pdf' | 'json' | 'markdown' | null;
  tags?: string[];
}

export interface TaskUpdateRequest {
  name?: string;
  description?: string | null;
  prompt_template?: string;
  template_variables?: Record<string, any>;
  tool_group_id?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  is_scheduled?: boolean;
  schedule_cron?: string | null;
  schedule_enabled?: boolean;
  generate_report?: boolean;
  report_format?: 'html' | 'pdf' | 'json' | 'markdown' | null;
  tags?: string[];
}

export interface TaskResponse {
  id: string;
  user_id: string;
  tool_group_id?: string | null;
  name: string;
  description?: string | null;
  prompt_template: string;
  allowed_tools: string[];
  disallowed_tools: string[];
  template_variables: Record<string, any>;
  is_scheduled: boolean;
  schedule_cron?: string | null;
  schedule_enabled: boolean;
  last_execution_at?: string | null;
  next_execution_at?: string | null;
  execution_count: number;
  success_count: number;
  failure_count: number;
  generate_report: boolean;
  report_format?: 'html' | 'pdf' | 'json' | 'markdown' | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  _links?: Links;
}

export interface TaskListResponse {
  items: TaskResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskExecuteRequest {
  variables?: Record<string, any>;
}

export interface TaskExecutionResponse {
  id: string;
  task_id: string;
  session_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  variables: Record<string, any>;
  report_id?: string | null;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface TaskExecutionListResponse {
  items: TaskExecutionResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// MCP Server Types
// ============================================================================

export interface MCPServerCreateRequest {
  name: string;
  description?: string | null;
  server_type: 'stdio' | 'sse' | 'http';
  config: Record<string, any>;
  is_enabled?: boolean;
}

export interface MCPServerUpdateRequest {
  description?: string | null;
  config?: Record<string, any>;
  is_enabled?: boolean;
}

export interface MCPServerResponse {
  id: string;
  name: string;
  description?: string | null;
  server_type: 'stdio' | 'sse' | 'http';
  config: Record<string, any>;
  user_id?: string | null;
  is_global: boolean;
  is_enabled: boolean;
  health_status?: 'healthy' | 'unhealthy' | 'unknown' | null;
  last_health_check_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MCPServerListResponse {
  items: MCPServerResponse[];
  total: number;
}

// ============================================================================
// Report Types
// ============================================================================

export interface ReportResponse {
  id: string;
  session_id: string;
  user_id: string;
  title: string;
  description?: string | null;
  report_type: 'task_execution' | 'manual' | 'scheduled' | 'auto_generated';
  content: Record<string, any>;
  file_path?: string | null;
  file_format?: 'html' | 'pdf' | 'json' | 'markdown' | null;
  file_size_bytes?: number | null;
  template_name?: string | null;
  tags: string[];
  task_execution_id?: string | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  _links?: Links;
}

export interface ReportListResponse {
  items: ReportResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

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

// ============================================================================
// Admin Types
// ============================================================================

export interface SystemStatsResponse {
  sessions: {
    total: number;
    active: number;
    completed_today: number;
  };
  tasks: {
    total: number;
    scheduled_enabled: number;
    executions_today: number;
  };
  users: {
    total: number;
    active_today: number;
  };
  cost: {
    total_usd: number;
    today_usd: number;
  };
  storage: {
    working_dirs_mb: number;
    reports_mb: number;
    archives_mb: number;
  };
}

export interface AdminUserResponse {
  id: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  deleted_at?: string | null;
  session_count?: number;
  task_count?: number;
}

export interface AdminUserListResponse {
  items: AdminUserResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Common Types
// ============================================================================

export interface Links {
  self?: string;
  [key: string]: string | undefined;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface APIError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}

// ============================================================================
// Utility Types
// ============================================================================

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
export type ReportFormat = 'html' | 'pdf' | 'json' | 'markdown';
export type MCPServerType = 'stdio' | 'sse' | 'http';
export type HealthStatus = 'healthy' | 'unhealthy' | 'unknown';
export type ArchiveStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
export type PermissionDecision = 'allow' | 'deny';
export type HookType = 'PreToolUse' | 'PostToolUse' | 'UserPromptSubmit' | 'Stop' | 'SubagentStop' | 'PreCompact';

// ============================================================================
// Task Template Types
// ============================================================================

export interface TaskTemplateResponse {
  id: string;
  name: string;
  description?: string;
  category?: string;
  icon?: string;
  prompt_template: string;
  template_variables_schema?: Record<string, any>;
  tool_group_id?: string | null;
  allowed_tools: string[];
  disallowed_tools: string[];
  sdk_options: Record<string, any>;
  generate_report: boolean;
  report_format?: string;
  tags: string[];
  is_public: boolean;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
  _links?: Links;
}

export interface TaskTemplateListResponse {
  items: TaskTemplateResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskTemplateCreateRequest {
  name: string;
  description?: string;
  category?: string;
  icon?: string;
  prompt_template: string;
  template_variables_schema?: Record<string, any>;
  tool_group_id?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  sdk_options?: Record<string, any>;
  generate_report?: boolean;
  report_format?: string;
  tags?: string[];
  is_public?: boolean;
  is_active?: boolean;
}

export interface TaskTemplateUpdateRequest {
  name?: string;
  description?: string;
  category?: string;
  icon?: string;
  prompt_template?: string;
  template_variables_schema?: Record<string, any>;
  tool_group_id?: string | null;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  sdk_options?: Record<string, any>;
  generate_report?: boolean;
  report_format?: string;
  tags?: string[];
  is_public?: boolean;
  is_active?: boolean;
}

export interface TaskTemplateStatsResponse {
  total_templates: number;
  active_templates: number;
  categories: Record<string, number>;
  most_used: TaskTemplateResponse[];
}

export interface CreateTaskFromTemplateRequest {
  name?: string;
  description?: string;
  tags?: string[];
  is_scheduled?: boolean;
  schedule_cron?: string;
  schedule_enabled?: boolean;
}

// ============================================================================
// Admin Types
// ============================================================================

export interface AdminUserItem {
  id: string;
  email: string;
  role: 'admin' | 'user';
  is_deleted: boolean;
  created_at: string;
}

export interface UserListResponse {
  items: AdminUserItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Monitoring Types
// ============================================================================

export interface BudgetStatusResponse {
  user_id: string;
  budget_limit: number;
  current_usage: number;
  remaining: number;
  period: string;
  alert_threshold: number;
  is_exceeded: boolean;
}

export interface StorageHealthResponse {
  status: HealthStatus;
  storage_available: boolean;
  disk_usage_percent: number;
  message?: string;
}
