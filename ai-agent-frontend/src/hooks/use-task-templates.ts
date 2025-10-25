import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  TaskTemplateCreateRequest,
  TaskTemplateUpdateRequest,
  TaskTemplateResponse,
  TaskTemplateListResponse,
  TaskTemplateStatsResponse,
  CreateTaskFromTemplateRequest,
  TaskResponse,
  PaginationParams,
} from '@/types/api';
import { toast } from 'sonner';

// Query Keys
const TASK_TEMPLATES_QUERY_KEY = 'task-templates';
const TASK_TEMPLATE_QUERY_KEY = 'task-template';
const TASK_TEMPLATE_STATS_QUERY_KEY = 'task-template-stats';

// ============================================================================
// Task Templates Queries
// ============================================================================

export function useTaskTemplates(params?: PaginationParams) {
  return useQuery({
    queryKey: [TASK_TEMPLATES_QUERY_KEY, params],
    queryFn: () => apiClient.listTaskTemplates(params),
  });
}

export function useTaskTemplate(templateId: string | undefined) {
  return useQuery({
    queryKey: [TASK_TEMPLATE_QUERY_KEY, templateId],
    queryFn: () => apiClient.getTaskTemplate(templateId!),
    enabled: !!templateId,
  });
}

export function useTaskTemplateStats() {
  return useQuery({
    queryKey: [TASK_TEMPLATE_STATS_QUERY_KEY],
    queryFn: () => apiClient.getTaskTemplateStats(),
  });
}

export function useTemplatesByCategory(category: string | undefined, params?: PaginationParams) {
  return useQuery({
    queryKey: [TASK_TEMPLATES_QUERY_KEY, 'category', category, params],
    queryFn: () => apiClient.getTemplatesByCategory(category!, params),
    enabled: !!category,
  });
}

// ============================================================================
// Task Templates Mutations
// ============================================================================

export function useCreateTaskTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TaskTemplateCreateRequest) => apiClient.createTaskTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATE_STATS_QUERY_KEY] });
      toast.success('Task template created successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create task template';
      toast.error(message);
    },
  });
}

export function useUpdateTaskTemplate(templateId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TaskTemplateUpdateRequest) => apiClient.updateTaskTemplate(templateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATE_QUERY_KEY, templateId] });
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATE_STATS_QUERY_KEY] });
      toast.success('Task template updated successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update task template';
      toast.error(message);
    },
  });
}

export function useDeleteTaskTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => apiClient.deleteTaskTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATE_STATS_QUERY_KEY] });
      toast.success('Task template deleted successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete task template';
      toast.error(message);
    },
  });
}

export function useCreateTaskFromTemplate(templateId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data?: CreateTaskFromTemplateRequest) => apiClient.createTaskFromTemplate(templateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TASK_TEMPLATE_QUERY_KEY, templateId] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] }); // Invalidate tasks list
      toast.success('Task created from template successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create task from template';
      toast.error(message);
    },
  });
}
