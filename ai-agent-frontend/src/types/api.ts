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
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// Session Types
// ============================================================================

export interface SessionCreateRequest {
  name?: string | null;
  description?: string | null;
  model?: string;
  allowed_tools?: string[];
  system_prompt?: string | null;
  mcp_servers?: string[];
  parent_session_id?: string | null;
}

export interface SessionResponse {
  id: string;
  user_id: string;
  name?: string | null;
  description?: string | null;
  status: 'active' | 'paused' | 'completed' | 'failed' | 'initializing';
  working_directory: string;
  allowed_tools: string[];
  system_prompt?: string | null;
  sdk_options: Record<string, any>;
  parent_session_id?: string | null;
  message_count: number;
  tool_call_count: number;
  total_cost_usd?: number | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  _links?: Links;
}

export interface SessionListResponse {
  items: SessionResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SessionQueryRequest {
  message: string;
  stream?: boolean;
}

export interface SessionQueryResponse {
  session_id: string;
  message_id: string;
  response: string;
  tool_calls?: ToolCallResponse[];
}

export interface SessionResumeRequest {
  resume_message?: string | null;
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

export interface ToolCallResponse {
  id: string;
  session_id: string;
  message_id: string;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output?: Record<string, any> | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

// ============================================================================
// Task Types
// ============================================================================

export interface TaskCreateRequest {
  name: string;
  description?: string | null;
  prompt_template: string;
  template_variables?: Record<string, any>;
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
  name: string;
  description?: string | null;
  prompt_template: string;
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

export interface AdminSessionListResponse {
  items: SessionResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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
// Session Template Types
// ============================================================================

export interface SessionTemplateCreateRequest {
  name: string;
  description?: string | null;
  category?: string | null;
  system_prompt?: string | null;
  working_directory?: string | null;
  allowed_tools?: string[] | null;
  sdk_options?: Record<string, any> | null;
  mcp_server_ids?: string[] | null;
  is_public?: boolean;
  is_organization_shared?: boolean;
  tags?: string[] | null;
  template_metadata?: Record<string, any> | null;
}

export interface SessionTemplateUpdateRequest {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  system_prompt?: string | null;
  working_directory?: string | null;
  allowed_tools?: string[] | null;
  sdk_options?: Record<string, any> | null;
  mcp_server_ids?: string[] | null;
  tags?: string[] | null;
  template_metadata?: Record<string, any> | null;
}

export interface SessionTemplateSharingUpdateRequest {
  is_public?: boolean | null;
  is_organization_shared?: boolean | null;
}

export interface SessionTemplateResponse {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  category?: string | null;
  system_prompt?: string | null;
  working_directory?: string | null;
  allowed_tools: string[];
  sdk_options: Record<string, any>;
  mcp_server_ids: string[];
  is_public: boolean;
  is_organization_shared: boolean;
  version: string;
  tags: string[];
  template_metadata: Record<string, any>;
  usage_count: number;
  last_used_at?: string | null;
  created_at: string;
  updated_at: string;
  _links?: Links;
}

export interface SessionTemplateListResponse {
  items: SessionTemplateResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SessionTemplateSearchRequest {
  search_term?: string | null;
  category?: string | null;
  tags?: string[] | null;
  page?: number;
  page_size?: number;
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

export type SessionStatus = 'active' | 'paused' | 'completed' | 'failed' | 'initializing';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
export type ReportFormat = 'html' | 'pdf' | 'json' | 'markdown';
export type MCPServerType = 'stdio' | 'sse' | 'http';
export type HealthStatus = 'healthy' | 'unhealthy' | 'unknown';
