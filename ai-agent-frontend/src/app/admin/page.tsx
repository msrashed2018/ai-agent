'use client';

import { AdminRoute } from '@/components/admin/admin-route';
import { StatsCard } from '@/components/admin/stats-card';
import { useSystemStats } from '@/hooks/use-admin';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Activity,
  Users,
  CheckCircle2,
  DollarSign,
  HardDrive,
  FileText,
  CalendarClock,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { formatCurrency, formatBytes } from '@/lib/utils';

function AdminDashboardContent() {
  const { data: stats, isLoading } = useSystemStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-1">System-wide statistics and management</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild>
            <Link href="/admin/sessions">All Sessions</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/admin/users">All Users</Link>
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {/* Sessions Stats */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Session Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatsCard
              title="Total Sessions"
              value={stats?.sessions.total ?? 0}
              icon={Activity}
              loading={isLoading}
              description="All time"
            />
            <StatsCard
              title="Active Sessions"
              value={stats?.sessions.active ?? 0}
              icon={TrendingUp}
              loading={isLoading}
              description="Currently running"
            />
            <StatsCard
              title="Completed Today"
              value={stats?.sessions.completed_today ?? 0}
              icon={CheckCircle2}
              loading={isLoading}
              description="Sessions finished today"
            />
          </div>
        </div>

        {/* Tasks Stats */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Task Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatsCard
              title="Total Tasks"
              value={stats?.tasks.total ?? 0}
              icon={FileText}
              loading={isLoading}
              description="All task templates"
            />
            <StatsCard
              title="Scheduled Tasks"
              value={stats?.tasks.scheduled_enabled ?? 0}
              icon={CalendarClock}
              loading={isLoading}
              description="Active scheduled tasks"
            />
            <StatsCard
              title="Executions Today"
              value={stats?.tasks.executions_today ?? 0}
              icon={Activity}
              loading={isLoading}
              description="Task runs today"
            />
          </div>
        </div>

        {/* Users & Cost */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-lg font-semibold mb-4">User Statistics</h2>
            <div className="grid grid-cols-2 gap-4">
              <StatsCard
                title="Total Users"
                value={stats?.users.total ?? 0}
                icon={Users}
                loading={isLoading}
                description="All registered users"
              />
              <StatsCard
                title="Active Today"
                value={stats?.users.active_today ?? 0}
                icon={Users}
                loading={isLoading}
                description="Users active today"
              />
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold mb-4">Cost Statistics</h2>
            <div className="grid grid-cols-2 gap-4">
              <StatsCard
                title="Total Cost"
                value={formatCurrency(stats?.cost.total_usd ?? 0)}
                icon={DollarSign}
                loading={isLoading}
                description="All time spending"
              />
              <StatsCard
                title="Today's Cost"
                value={formatCurrency(stats?.cost.today_usd ?? 0)}
                icon={DollarSign}
                loading={isLoading}
                description="Costs incurred today"
              />
            </div>
          </div>
        </div>

        {/* Storage Stats */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Storage Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatsCard
              title="Working Directories"
              value={`${stats?.storage.working_dirs_mb ?? 0} MB`}
              icon={HardDrive}
              loading={isLoading}
              description="Session working directories"
            />
            <StatsCard
              title="Reports"
              value={`${stats?.storage.reports_mb ?? 0} MB`}
              icon={FileText}
              loading={isLoading}
              description="Generated reports"
            />
            <StatsCard
              title="Archives"
              value={`${stats?.storage.archives_mb ?? 0} MB`}
              icon={HardDrive}
              loading={isLoading}
              description="Archived data"
            />
          </div>
        </div>

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
            <CardDescription>Jump to admin management pages</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start h-auto p-4" asChild>
              <Link href="/admin/sessions">
                <div className="flex flex-col items-start gap-1 text-left">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <span className="font-semibold">All Sessions</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    View and manage all user sessions
                  </span>
                </div>
              </Link>
            </Button>
            <Button variant="outline" className="justify-start h-auto p-4" asChild>
              <Link href="/admin/users">
                <div className="flex flex-col items-start gap-1 text-left">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    <span className="font-semibold">All Users</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Manage users and permissions
                  </span>
                </div>
              </Link>
            </Button>
            <Button variant="outline" className="justify-start h-auto p-4" asChild>
              <Link href="/dashboard">
                <div className="flex flex-col items-start gap-1 text-left">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <span className="font-semibold">User Dashboard</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Switch to user view
                  </span>
                </div>
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  return (
    <AdminRoute>
      <AdminDashboardContent />
    </AdminRoute>
  );
}
