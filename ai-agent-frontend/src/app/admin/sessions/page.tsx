'use client';

import { useState } from 'react';
import { AdminRoute } from '@/components/admin/admin-route';
import { useAllSessions, useAllUsers } from '@/hooks/use-admin';
import { UserAvatar } from '@/components/admin/user-avatar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Search } from 'lucide-react';
import Link from 'next/link';
import { formatDate, formatCurrency, getStatusColor } from '@/lib/utils';

function AllSessionsContent() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [userIdFilter, setUserIdFilter] = useState<string | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch sessions and users
  const { data: sessions, isLoading: sessionsLoading } = useAllSessions({
    page,
    page_size: 20,
    status: statusFilter,
    user_id: userIdFilter,
  });

  const { data: usersData } = useAllUsers({ page: 1, page_size: 1000 });

  // Create user lookup map
  const userMap = new Map<string, any>(
    usersData?.items?.map((user: any) => [user.id, user]) ?? []
  );

  // Filter sessions by search term (session name)
  const filteredSessions = sessions?.items.filter((session) =>
    session.name?.toLowerCase().includes(searchTerm.toLowerCase())
  ) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/admin">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Admin
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">All Sessions</h1>
            <p className="text-muted-foreground mt-1">
              View and manage sessions across all users
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter sessions by status, user, or name</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search by name */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by session name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Status filter */}
            <Select
              value={statusFilter ?? 'all'}
              onValueChange={(value) => {
                setStatusFilter(value === 'all' ? undefined : value);
                setPage(1);
              }}
            >
              <SelectTrigger>
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

            {/* User filter */}
            <Select
              value={userIdFilter ?? 'all'}
              onValueChange={(value) => {
                setUserIdFilter(value === 'all' ? undefined : value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filter by user" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Users</SelectItem>
                {usersData?.items?.map((user: any) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.email}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Sessions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Sessions</CardTitle>
              <CardDescription>
                {sessions?.total ?? 0} total sessions
                {statusFilter && ` with status "${statusFilter}"`}
                {userIdFilter && ` for selected user`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No sessions found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Session Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead className="text-right">Messages</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => {
                    const user = userMap.get(session.user_id);
                    return (
                      <TableRow key={session.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <UserAvatar email={user?.email ?? 'Unknown'} size="sm" />
                            <div className="flex flex-col">
                              <span className="text-sm font-medium">
                                {user?.email ?? 'Unknown User'}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {user?.role ? (
                                  <Badge variant="outline" className="text-xs">
                                    {user.role}
                                  </Badge>
                                ) : null}
                              </span>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium">
                              {session.name || 'Untitled Session'}
                            </span>
                            {session.description && (
                              <span className="text-xs text-muted-foreground">
                                {session.description.substring(0, 50)}
                                {session.description.length > 50 ? '...' : ''}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(session.status)}>
                            {session.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {session.sdk_options?.model ?? 'claude-sonnet-4'}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          {session.message_count}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(session.total_cost_usd ?? 0)}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">{formatDate(session.created_at)}</span>
                        </TableCell>
                        <TableCell>
                          <Button variant="outline" size="sm" asChild>
                            <Link href={`/sessions/${session.id}`}>View</Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {sessions && sessions.total_pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {sessions.total_pages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(sessions.total_pages, p + 1))}
                      disabled={page === sessions.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AllSessionsPage() {
  return (
    <AdminRoute>
      <AllSessionsContent />
    </AdminRoute>
  );
}
