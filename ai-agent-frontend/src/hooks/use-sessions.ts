import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  SessionCreateRequest,
  SessionResponse,
  SessionListResponse,
  SessionQueryRequest,
  SessionQueryResponse,
  MessageResponse,
  ToolCallResponse,
  PaginationParams,
} from '@/types/api';
import { toast } from 'sonner';

// Query Keys
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (params?: PaginationParams & { status?: string; search?: string }) =>
    [...sessionKeys.lists(), params] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
  messages: (id: string) => [...sessionKeys.detail(id), 'messages'] as const,
  toolCalls: (id: string) => [...sessionKeys.detail(id), 'tool-calls'] as const,
};

// ============================================================================
// Queries
// ============================================================================

export function useSessions(params?: PaginationParams & { status?: string; search?: string }) {
  return useQuery({
    queryKey: sessionKeys.list(params),
    queryFn: () => apiClient.listSessions(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useSession(sessionId: string) {
  return useQuery({
    queryKey: sessionKeys.detail(sessionId),
    queryFn: () => apiClient.getSession(sessionId),
    enabled: !!sessionId,
    staleTime: 10000, // 10 seconds
  });
}

export function useSessionMessages(sessionId: string) {
  return useQuery({
    queryKey: sessionKeys.messages(sessionId),
    queryFn: () => apiClient.getSessionMessages(sessionId),
    enabled: !!sessionId,
    staleTime: 5000, // 5 seconds
  });
}

export function useSessionToolCalls(sessionId: string) {
  return useQuery({
    queryKey: sessionKeys.toolCalls(sessionId),
    queryFn: () => apiClient.getSessionToolCalls(sessionId),
    enabled: !!sessionId,
    staleTime: 5000, // 5 seconds
  });
}

// ============================================================================
// Mutations
// ============================================================================

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionCreateRequest) => apiClient.createSession(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
      toast.success('Session created successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create session';
      toast.error(message);
    },
  });
}

export function useQuerySession(sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionQueryRequest) => apiClient.querySession(sessionId, data),
    onSuccess: () => {
      // Invalidate messages and tool calls to fetch the new ones
      queryClient.invalidateQueries({ queryKey: sessionKeys.messages(sessionId) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.toolCalls(sessionId) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to send message';
      toast.error(message);
    },
  });
}

export function usePauseSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => apiClient.pauseSession(sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
      toast.success('Session paused');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to pause session';
      toast.error(message);
    },
  });
}

export function useResumeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, resume_message }: { sessionId: string; resume_message?: string }) =>
      apiClient.resumeSession(sessionId, { resume_message }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
      toast.success('Session resumed');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to resume session';
      toast.error(message);
    },
  });
}

export function useDownloadWorkdir() {
  return useMutation({
    mutationFn: (sessionId: string) => apiClient.downloadWorkdir(sessionId),
    onSuccess: (blob, sessionId) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session-${sessionId}-workdir.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Working directory downloaded');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to download working directory';
      toast.error(message);
    },
  });
}
