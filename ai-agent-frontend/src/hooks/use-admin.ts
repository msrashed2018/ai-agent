import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  SystemStatsResponse,
  PaginationParams,
} from '@/types/api';

// Query Keys
export const adminKeys = {
  all: ['admin'] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
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
// All Users (Admin View)
// ============================================================================

export function useAllUsers(params?: PaginationParams & { include_deleted?: boolean }) {
  return useQuery({
    queryKey: adminKeys.userList(params),
    queryFn: () => apiClient.listAllUsers(params),
    staleTime: 30000, // 30 seconds
  });
}
