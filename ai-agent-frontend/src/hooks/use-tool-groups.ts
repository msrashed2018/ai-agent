import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  ToolGroupCreateRequest,
  ToolGroupUpdateRequest,
  ToolGroupResponse,
  ToolGroupListResponse,
  PaginationParams,
} from '@/types/api';
import { toast } from 'sonner';

// Query Keys
const TOOL_GROUPS_QUERY_KEY = 'tool-groups';
const TOOL_GROUP_QUERY_KEY = 'tool-group';

// ============================================================================
// Tool Groups Queries
// ============================================================================

export function useToolGroups(params?: PaginationParams) {
  return useQuery({
    queryKey: [TOOL_GROUPS_QUERY_KEY, params],
    queryFn: () => apiClient.listToolGroups(params),
  });
}

export function useToolGroup(toolGroupId: string | undefined) {
  return useQuery({
    queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId],
    queryFn: () => apiClient.getToolGroup(toolGroupId!),
    enabled: !!toolGroupId,
  });
}

// ============================================================================
// Tool Groups Mutations
// ============================================================================

export function useCreateToolGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ToolGroupCreateRequest) => apiClient.createToolGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool group created successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create tool group';
      toast.error(message);
    },
  });
}

export function useUpdateToolGroup(toolGroupId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ToolGroupUpdateRequest) => apiClient.updateToolGroup(toolGroupId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId] });
      toast.success('Tool group updated successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update tool group';
      toast.error(message);
    },
  });
}

export function useDeleteToolGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (toolGroupId: string) => apiClient.deleteToolGroup(toolGroupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool group deleted successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete tool group';
      toast.error(message);
    },
  });
}

export function useAddAllowedTool(toolGroupId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tool: string) => apiClient.addAllowedTool(toolGroupId, tool),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId] });
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool added to allowed list');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to add allowed tool';
      toast.error(message);
    },
  });
}

export function useRemoveAllowedTool(toolGroupId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tool: string) => apiClient.removeAllowedTool(toolGroupId, tool),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId] });
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool removed from allowed list');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to remove allowed tool';
      toast.error(message);
    },
  });
}

export function useAddDisallowedTool(toolGroupId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tool: string) => apiClient.addDisallowedTool(toolGroupId, tool),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId] });
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool added to disallowed list');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to add disallowed tool';
      toast.error(message);
    },
  });
}

export function useRemoveDisallowedTool(toolGroupId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tool: string) => apiClient.removeDisallowedTool(toolGroupId, tool),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUP_QUERY_KEY, toolGroupId] });
      queryClient.invalidateQueries({ queryKey: [TOOL_GROUPS_QUERY_KEY] });
      toast.success('Tool removed from disallowed list');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to remove disallowed tool';
      toast.error(message);
    },
  });
}
