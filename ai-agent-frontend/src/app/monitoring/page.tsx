'use client';

import { useAuthStore } from '@/store/auth-store';
import { useSystemHealth, useDatabaseHealth, useSDKHealth, useStorageHealth, useUserCosts, useUserBudget } from '@/hooks/use-monitoring';
import { HealthStatusCard, CostCard, BudgetCard, StorageHealthCard } from '@/components/monitoring';
import { redirect } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function MonitoringPage() {
  const { user, isLoading, loadUser } = useAuthStore();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!isLoading) {
      if (!user || user.role !== 'admin') {
        redirect('/dashboard');
      } else {
        setIsAdmin(true);
      }
    }
  }, [user, isLoading]);

  // Health monitoring hooks
  const { data: systemHealth, isLoading: systemHealthLoading, error: systemHealthError } = useSystemHealth();
  const { data: dbHealth, isLoading: dbHealthLoading, error: dbHealthError } = useDatabaseHealth();
  const { data: sdkHealth, isLoading: sdkHealthLoading, error: sdkHealthError } = useSDKHealth();
  const { data: storageHealth, isLoading: storageHealthLoading, error: storageHealthError } = useStorageHealth();

  // Cost & Budget hooks
  const { data: todayCosts, isLoading: todaysCostsLoading } = useUserCosts(user?.id, 'today');
  const { data: weekCosts, isLoading: weekCostsLoading } = useUserCosts(user?.id, 'week');
  const { data: monthCosts, isLoading: monthCostsLoading } = useUserCosts(user?.id, 'month');
  const { data: budget, isLoading: budgetLoading } = useUserBudget(user?.id);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">System Monitoring</h1>
          <p className="text-lg text-gray-600">Monitor system health, costs, budgets, and performance metrics</p>
        </div>

        {/* Health Status Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <HealthStatusCard
              title="System Status"
              health={systemHealth}
              isLoading={systemHealthLoading}
              error={systemHealthError}
            />
            <HealthStatusCard
              title="Database Status"
              health={dbHealth}
              isLoading={dbHealthLoading}
              error={dbHealthError}
            />
            <HealthStatusCard
              title="SDK Status"
              health={sdkHealth}
              isLoading={sdkHealthLoading}
              error={sdkHealthError}
            />
            <StorageHealthCard
              storage={storageHealth}
              isLoading={storageHealthLoading}
              error={storageHealthError}
            />
          </div>
        </div>

        {/* Costs Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Cost Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <CostCard
              title="Today's Cost"
              costs={todayCosts}
              isLoading={todaysCostsLoading}
              period="today"
            />
            <CostCard
              title="This Week's Cost"
              costs={weekCosts}
              isLoading={weekCostsLoading}
              period="week"
            />
            <CostCard
              title="This Month's Cost"
              costs={monthCosts}
              isLoading={monthCostsLoading}
              period="month"
            />
          </div>
        </div>

        {/* Budget Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Budget Status</h2>
          <div className="max-w-2xl">
            <BudgetCard
              budget={budget}
              isLoading={budgetLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
