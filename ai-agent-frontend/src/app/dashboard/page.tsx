'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { StatCard } from '@/components/dashboard/stat-card';
import { RecentSessionsTable } from '@/components/dashboard/recent-sessions-table';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, CheckCircle2, DollarSign, FileText, PlayCircle, Plus } from 'lucide-react';
import Link from 'next/link';
import { formatCurrency } from '@/lib/utils';

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => apiClient.listSessions({ page: 1, page_size: 100 }),
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => apiClient.listTasks({ page: 1, page_size: 100 }),
  });

  // Calculate stats
  const totalSessions = sessions?.total || 0;
  const totalTasks = tasks?.total || 0;
  const activeSessions =
    sessions?.items.filter((s) => s.status === 'active' || s.status === 'initializing').length || 0;
  const totalCost =
    sessions?.items.reduce((acc, s) => acc + (s.total_cost_usd || 0), 0) || 0;

  // Get recent sessions (last 5)
  const recentSessions = sessions?.items.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back, {user?.email}</p>
        </div>
        <Button asChild>
          <Link href="/sessions/new">
            <Plus className="mr-2 h-4 w-4" />
            New Session
          </Link>
        </Button>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Sessions"
            value={totalSessions}
            icon={Activity}
            loading={sessionsLoading}
            subtitle="All time"
          />
          <StatCard
            title="Active Sessions"
            value={activeSessions}
            icon={PlayCircle}
            loading={sessionsLoading}
            subtitle="Currently running"
          />
          <StatCard
            title="Total Tasks"
            value={totalTasks}
            icon={FileText}
            loading={tasksLoading}
            subtitle="Task templates"
          />
          <StatCard
            title="Total Cost"
            value={formatCurrency(totalCost)}
            icon={DollarSign}
            loading={sessionsLoading}
            subtitle="All sessions"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Sessions */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Recent Sessions</CardTitle>
                    <CardDescription>Your latest Claude Code sessions</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/sessions">View All</Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <RecentSessionsTable sessions={recentSessions} loading={sessionsLoading} />
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common tasks and shortcuts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start" variant="outline" asChild>
                  <Link href="/sessions/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Create New Session
                  </Link>
                </Button>
                <Button className="w-full justify-start" variant="outline" asChild>
                  <Link href="/tasks/new">
                    <FileText className="mr-2 h-4 w-4" />
                    Create New Task
                  </Link>
                </Button>
                <Button className="w-full justify-start" variant="outline" asChild>
                  <Link href="/sessions">
                    <Activity className="mr-2 h-4 w-4" />
                    View All Sessions
                  </Link>
                </Button>
                <Button className="w-full justify-start" variant="outline" asChild>
                  <Link href="/tasks">
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    View All Tasks
                  </Link>
                </Button>
              </CardContent>
            </Card>

            {/* Session Stats */}
            {sessions && sessions.items.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Session Statistics</CardTitle>
                  <CardDescription>Breakdown by status</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {['active', 'completed', 'failed', 'paused'].map((status) => {
                    const count = sessions.items.filter((s) => s.status === status).length;
                    const percentage = totalSessions > 0 ? (count / totalSessions) * 100 : 0;
                    return (
                      <div key={status} className="flex items-center justify-between text-sm">
                        <span className="capitalize text-gray-600">{status}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                status === 'active'
                                  ? 'bg-green-600'
                                  : status === 'completed'
                                  ? 'bg-blue-600'
                                  : status === 'failed'
                                  ? 'bg-red-600'
                                  : 'bg-yellow-600'
                              }`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="font-medium w-8 text-right">{count}</span>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
