import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import {
  MCPServerCreateRequest,
  MCPServerUpdateRequest,
  MCPServerResponse,
  MCPServerListResponse,
} from '@/types/api';
import { toast } from 'sonner';

export function useMCPServers() {
  return useQuery<MCPServerListResponse>({
    queryKey: ['mcp-servers'],
    queryFn: () => apiClient.listMCPServers(),
  });
}

export function useMCPServer(serverId: string) {
  return useQuery<MCPServerResponse>({
    queryKey: ['mcp-servers', serverId],
    queryFn: () => apiClient.getMCPServer(serverId),
    enabled: !!serverId,
  });
}

export function useCreateMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MCPServerCreateRequest) => apiClient.createMCPServer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      toast.success('MCP server created successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create MCP server');
    },
  });
}

export function useUpdateMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ serverId, data }: { serverId: string; data: MCPServerUpdateRequest }) =>
      apiClient.updateMCPServer(serverId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      queryClient.invalidateQueries({ queryKey: ['mcp-servers', variables.serverId] });
      toast.success('MCP server updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update MCP server');
    },
  });
}

export function useDeleteMCPServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serverId: string) => apiClient.deleteMCPServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      toast.success('MCP server deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete MCP server');
    },
  });
}

export function useHealthCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serverId: string) => apiClient.healthCheckMCPServer(serverId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      queryClient.invalidateQueries({ queryKey: ['mcp-servers', data.id] });

      if (data.health_status === 'healthy') {
        toast.success('Server is healthy');
      } else if (data.health_status === 'unhealthy') {
        toast.error('Server is unhealthy');
      } else {
        toast.info('Server health status is unknown');
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Health check failed');
    },
  });
}

export function useMCPTemplates() {
  return useQuery({
    queryKey: ['mcp-templates'],
    queryFn: () => apiClient.getMCPTemplates(),
  });
}

export function useImportConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, overrideExisting }: { file: File; overrideExisting: boolean }) =>
      apiClient.importMCPConfig(file, overrideExisting),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      const imported = data.imported || 0;
      const skipped = data.skipped || 0;
      const errors = data.errors || 0;
      toast.success(
        `Import complete: ${imported} imported, ${skipped} skipped, ${errors} errors`
      );
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to import configuration');
    },
  });
}

export function useExportConfig() {
  return useMutation({
    mutationFn: (includeGlobal: boolean = true) => apiClient.exportMCPConfig(includeGlobal),
    onSuccess: (data) => {
      // Create blob and download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'claude_desktop_config.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success('Configuration exported successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to export configuration');
    },
  });
}
