import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  HealthCheckResponse,
  StorageHealthResponse,
  CostSummaryResponse,
  BudgetStatusResponse,
  SystemStatsResponse,
} from '@/types/api';

// Query Keys
const MONITORING_QUERY_KEY = 'monitoring';
const HEALTH_QUERY_KEY = 'health';
const HEALTH_DB_QUERY_KEY = 'health-db';
const HEALTH_SDK_QUERY_KEY = 'health-sdk';
const HEALTH_STORAGE_QUERY_KEY = 'health-storage';
const COSTS_QUERY_KEY = 'costs';
const BUDGET_QUERY_KEY = 'budget';
const SYSTEM_STATS_QUERY_KEY = 'system-stats';

// ============================================================================
// System Health Queries
// ============================================================================

export function useSystemHealth() {
  return useQuery({
    queryKey: [HEALTH_QUERY_KEY],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useDatabaseHealth() {
  return useQuery({
    queryKey: [HEALTH_DB_QUERY_KEY],
    queryFn: () => apiClient.getDatabaseHealth(),
    refetchInterval: 30000,
  });
}

export function useSDKHealth() {
  return useQuery({
    queryKey: [HEALTH_SDK_QUERY_KEY],
    queryFn: () => apiClient.getSDKHealth(),
    refetchInterval: 30000,
  });
}

export function useStorageHealth() {
  return useQuery({
    queryKey: [HEALTH_STORAGE_QUERY_KEY],
    queryFn: () => apiClient.getStorageHealth(),
    refetchInterval: 30000,
  });
}

// ============================================================================
// Cost & Budget Queries
// ============================================================================

export function useUserCosts(userId: string | undefined, period: 'today' | 'week' | 'month' = 'today') {
  return useQuery({
    queryKey: [COSTS_QUERY_KEY, userId, period],
    queryFn: () => apiClient.getUserCosts(userId!, period),
    enabled: !!userId,
    refetchInterval: 60000, // Refetch every 60 seconds
  });
}

export function useUserBudget(userId: string | undefined) {
  return useQuery({
    queryKey: [BUDGET_QUERY_KEY, userId],
    queryFn: () => apiClient.getUserBudgetStatus(userId!),
    enabled: !!userId,
    refetchInterval: 60000,
  });
}

// ============================================================================
// System Statistics Queries
// ============================================================================

export function useSystemStats() {
  return useQuery({
    queryKey: [SYSTEM_STATS_QUERY_KEY],
    queryFn: () => apiClient.getSystemStats(),
    refetchInterval: 60000,
  });
}
