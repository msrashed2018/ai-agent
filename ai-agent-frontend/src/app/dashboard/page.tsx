'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { StatCard } from '@/components/dashboard/stat-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, CheckCircle2, DollarSign, FileText, PlayCircle, Plus } from 'lucide-react';
import Link from 'next/link';
import { formatCurrency } from '@/lib/utils';

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => apiClient.listTasks({ page: 1, page_size: 100 }),
  });

  // Calculate stats
  const totalTasks = tasks?.total || 0;
  const scheduledTasks = tasks?.items.filter((t) => t.is_scheduled && t.schedule_enabled).length || 0;
  const tasksWithExecutions = tasks?.items.filter((t) => t.execution_count > 0).length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back, {user?.email}</p>
        </div>
        <Button asChild>
          <Link href="/tasks/new">
            <Plus className="mr-2 h-4 w-4" />
            New Task
          </Link>
        </Button>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="Total Tasks"
            value={totalTasks}
            icon={FileText}
            loading={tasksLoading}
            subtitle="All task templates"
          />
          <StatCard
            title="Executed Tasks"
            value={tasksWithExecutions}
            icon={Activity}
            loading={tasksLoading}
            subtitle="Tasks with executions"
          />
          <StatCard
            title="Scheduled Tasks"
            value={scheduledTasks}
            icon={CheckCircle2}
            loading={tasksLoading}
            subtitle="Automated execution"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common tasks and operations</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button asChild variant="outline" className="h-20 flex-col gap-2">
                  <Link href="/tasks/new">
                    <Plus className="h-5 w-5" />
                    <span>Create New Task</span>
                  </Link>
                </Button>
                <Button asChild variant="outline" className="h-20 flex-col gap-2">
                  <Link href="/tasks">
                    <FileText className="h-5 w-5" />
                    <span>View All Tasks</span>
                  </Link>
                </Button>
                <Button asChild variant="outline" className="h-20 flex-col gap-2">
                  <Link href="/reports">
                    <Activity className="h-5 w-5" />
                    <span>View Reports</span>
                  </Link>
                </Button>
                <Button asChild variant="outline" className="h-20 flex-col gap-2">
                  <Link href="/mcp-servers">
                    <PlayCircle className="h-5 w-5" />
                    <span>MCP Servers</span>
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Getting Started */}
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>New to the AI Agent platform?</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">1. Create a Task</h4>
                <p className="text-sm text-muted-foreground">
                  Define reusable task templates with prompts and automation
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">2. Execute Tasks</h4>
                <p className="text-sm text-muted-foreground">
                  Run tasks manually or schedule them for automation
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">3. View Reports</h4>
                <p className="text-sm text-muted-foreground">
                  Review generated reports and execution results
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
