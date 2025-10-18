import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import type {
  SessionTemplateCreateRequest,
  SessionTemplateUpdateRequest,
  SessionTemplateSharingUpdateRequest,
  SessionTemplateSearchRequest,
  PaginationParams,
} from '@/types/api';

// ============================================================================
// Query Hooks
// ============================================================================

export function useSessionTemplates(params?: PaginationParams) {
  return useQuery({
    queryKey: ['session-templates', params],
    queryFn: () => apiClient.listSessionTemplates(params),
  });
}

export function useSessionTemplate(templateId: string | undefined) {
  return useQuery({
    queryKey: ['session-templates', templateId],
    queryFn: () => apiClient.getSessionTemplate(templateId!),
    enabled: !!templateId,
  });
}

export function usePopularTemplates() {
  return useQuery({
    queryKey: ['session-templates', 'popular'],
    queryFn: () => apiClient.getPopularTemplates(),
  });
}

export function useSearchTemplates(searchParams: SessionTemplateSearchRequest) {
  return useQuery({
    queryKey: ['session-templates', 'search', searchParams],
    queryFn: () => apiClient.searchSessionTemplates(searchParams),
    enabled: !!(searchParams.search_term || searchParams.category || searchParams.tags?.length),
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionTemplateCreateRequest) => apiClient.createSessionTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session-templates'] });
      toast.success('Template created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create template');
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: string; data: SessionTemplateUpdateRequest }) =>
      apiClient.updateSessionTemplate(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['session-templates'] });
      queryClient.invalidateQueries({ queryKey: ['session-templates', variables.templateId] });
      toast.success('Template updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update template');
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => apiClient.deleteSessionTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session-templates'] });
      toast.success('Template deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete template');
    },
  });
}

export function useUpdateTemplateSharing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: string; data: SessionTemplateSharingUpdateRequest }) =>
      apiClient.updateSessionTemplateSharing(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['session-templates'] });
      queryClient.invalidateQueries({ queryKey: ['session-templates', variables.templateId] });
      toast.success('Sharing settings updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update sharing settings');
    },
  });
}

// ============================================================================
// Helper Hooks
// ============================================================================

export function useTemplateCategories() {
  // Common template categories
  return [
    'development',
    'security',
    'production',
    'debugging',
    'performance',
    'custom',
  ];
}
