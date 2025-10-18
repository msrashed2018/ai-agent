'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SessionTable } from '@/components/sessions/session-table';
import { CreateSessionDialog } from '@/components/sessions/create-session-dialog';
import { useSessions, usePauseSession, useResumeSession } from '@/hooks/use-sessions';
import { Plus, Search } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function SessionsPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [page, setPage] = React.useState(1);
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);

  const pageSize = 10;

  // Fetch sessions with filters
  const { data, isLoading, error } = useSessions({
    page,
    page_size: pageSize,
    status: statusFilter === 'all' ? undefined : statusFilter,
  });

  const pauseSession = usePauseSession();
  const resumeSession = useResumeSession();

  // Filter sessions by search query (client-side filtering for now)
  const filteredSessions = React.useMemo(() => {
    if (!data?.items) return [];
    if (!searchQuery) return data.items;

    const query = searchQuery.toLowerCase();
    return data.items.filter(
      (session) =>
        session.name?.toLowerCase().includes(query) ||
        session.description?.toLowerCase().includes(query) ||
        session.id.toLowerCase().includes(query)
    );
  }, [data?.items, searchQuery]);

  const handlePause = async (sessionId: string) => {
    await pauseSession.mutateAsync(sessionId);
  };

  const handleResume = async (sessionId: string) => {
    await resumeSession.mutateAsync({ sessionId });
  };

  const handleDelete = async (sessionId: string) => {
    if (confirm('Are you sure you want to delete this session?')) {
      // TODO: Implement delete functionality
      console.log('Delete session:', sessionId);
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sessions</h1>
          <p className="text-gray-500 mt-1">
            Manage your AI agent sessions and conversations
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Session
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Status Filter */}
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="initializing">Initializing</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load sessions. Please try again.
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {/* Sessions Table */}
      {!isLoading && !error && (
        <>
          <SessionTable
            sessions={filteredSessions}
            onPause={handlePause}
            onResume={handleResume}
            onDelete={handleDelete}
          />

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, data.total)} of {data.total} sessions
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create Dialog */}
      <CreateSessionDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
    </div>
  );
}
