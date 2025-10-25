import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskResponse,
  TaskListResponse,
  TaskExecuteRequest,
  TaskExecutionResponse,
  TaskExecutionListResponse,
  PaginationParams,
  ExecutionCancelRequest,
  ToolCallListResponse,
  WorkingDirectoryManifest,
  ArchiveResponse,
} from '@/types/api';
import { toast } from 'sonner';

// Query Keys
const TASKS_QUERY_KEY = 'tasks';
const TASK_QUERY_KEY = 'task';
const TASK_EXECUTIONS_QUERY_KEY = 'task-executions';
const TASK_EXECUTION_QUERY_KEY = 'task-execution';
const EXECUTION_TOOL_CALLS_QUERY_KEY = 'execution-tool-calls';
const EXECUTION_FILES_QUERY_KEY = 'execution-files';

interface UseTasksParams extends PaginationParams {
  tags?: string[];
  is_scheduled?: boolean;
}

// ============================================================================
// Tasks Queries
// ============================================================================

export function useTasks(params?: UseTasksParams) {
  return useQuery({
    queryKey: [TASKS_QUERY_KEY, params],
    queryFn: () => apiClient.listTasks(params),
  });
}

export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: [TASK_QUERY_KEY, taskId],
    queryFn: () => apiClient.getTask(taskId!),
    enabled: !!taskId,
  });
}

// ============================================================================
// Task Mutations
// ============================================================================

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TaskCreateRequest) => apiClient.createTask(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
      toast.success('Task created successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create task';
      toast.error(message);
    },
  });
}

export function useUpdateTask(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TaskUpdateRequest) => apiClient.updateTask(taskId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TASK_QUERY_KEY, taskId] });
      toast.success('Task updated successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update task';
      toast.error(message);
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => apiClient.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASKS_QUERY_KEY] });
      toast.success('Task deleted successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete task';
      toast.error(message);
    },
  });
}

export function useExecuteTask(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data?: TaskExecuteRequest) => apiClient.executeTask(taskId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [TASK_QUERY_KEY, taskId] });
      queryClient.invalidateQueries({ queryKey: [TASK_EXECUTIONS_QUERY_KEY, taskId] });
      toast.success('Task execution started');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to execute task';
      toast.error(message);
    },
  });
}

// ============================================================================
// Task Executions Queries
// ============================================================================

export function useTaskExecutions(taskId: string | undefined, params?: PaginationParams) {
  return useQuery({
    queryKey: [TASK_EXECUTIONS_QUERY_KEY, taskId, params],
    queryFn: () => apiClient.listTaskExecutions(taskId!, params),
    enabled: !!taskId,
  });
}

export function useTaskExecution(executionId: string | undefined) {
  return useQuery({
    queryKey: [TASK_EXECUTION_QUERY_KEY, executionId],
    queryFn: () => apiClient.getTaskExecution(executionId!),
    enabled: !!executionId,
    refetchInterval: (query) => {
      // Auto-refresh if execution is pending or running
      const data = query.state.data;
      if (data && (data.status === 'pending' || data.status === 'running')) {
        return 2000; // Poll every 2 seconds
      }
      return false;
    },
  });
}

// ============================================================================
// Execution Mutations - Retry, Cancel, Files, Archive
// ============================================================================

export function useRetryExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => apiClient.retryTaskExecution(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_EXECUTION_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TASK_EXECUTIONS_QUERY_KEY] });
      toast.success('Execution retried successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to retry execution';
      toast.error(message);
    },
  });
}

export function useCancelExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ executionId, data }: { executionId: string; data?: ExecutionCancelRequest }) =>
      apiClient.cancelExecution(executionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_EXECUTION_QUERY_KEY] });
      toast.success('Execution cancelled successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to cancel execution';
      toast.error(message);
    },
  });
}

export function useExecutionToolCalls(executionId: string | undefined, params?: PaginationParams) {
  return useQuery({
    queryKey: [EXECUTION_TOOL_CALLS_QUERY_KEY, executionId, params],
    queryFn: () => apiClient.getExecutionToolCalls(executionId!, params),
    enabled: !!executionId,
  });
}

export function useExecutionFiles(executionId: string | undefined) {
  return useQuery({
    queryKey: [EXECUTION_FILES_QUERY_KEY, executionId],
    queryFn: () => apiClient.getExecutionFiles(executionId!),
    enabled: !!executionId,
  });
}

export function useDownloadExecutionFile() {
  return useMutation({
    mutationFn: ({ executionId, filePath }: { executionId: string; filePath: string }) =>
      apiClient.downloadExecutionFile(executionId, filePath),
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to download file';
      toast.error(message);
    },
  });
}

export function useArchiveExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => apiClient.archiveExecutionDirectory(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXECUTION_FILES_QUERY_KEY] });
      toast.success('Execution directory archived successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to archive directory';
      toast.error(message);
    },
  });
}

export function useDownloadArchive() {
  return useMutation({
    mutationFn: (executionId: string) => apiClient.downloadArchive(executionId),
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to download archive';
      toast.error(message);
    },
  });
}
