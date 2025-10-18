import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  SystemStatsResponse,
  AdminSessionListResponse,
  PaginationParams,
} from '@/types/api';

// Query Keys
export const adminKeys = {
  all: ['admin'] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
  sessions: () => [...adminKeys.all, 'sessions'] as const,
  sessionList: (params?: PaginationParams & { user_id?: string; status?: string }) =>
    [...adminKeys.sessions(), params] as const,
  users: () => [...adminKeys.all, 'users'] as const,
  userList: (params?: PaginationParams & { include_deleted?: boolean }) =>
    [...adminKeys.users(), params] as const,
};

// ============================================================================
// System Stats
// ============================================================================

export function useSystemStats() {
  return useQuery({
    queryKey: adminKeys.stats(),
    queryFn: () => apiClient.getSystemStats(),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
}

// ============================================================================
// All Sessions (Admin View)
// ============================================================================

export function useAllSessions(params?: PaginationParams & { user_id?: string; status?: string }) {
  return useQuery({
    queryKey: adminKeys.sessionList(params),
    queryFn: () => apiClient.listAllSessions(params),
    staleTime: 30000, // 30 seconds
  });
}

// ============================================================================
// All Users (Admin View)
// ============================================================================

export function useAllUsers(params?: PaginationParams & { include_deleted?: boolean }) {
  return useQuery({
    queryKey: adminKeys.userList(params),
    queryFn: () => apiClient.listAllUsers(params),
    staleTime: 30000, // 30 seconds
  });
}
