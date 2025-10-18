'use client';

import { useState } from 'react';
import { AdminRoute } from '@/components/admin/admin-route';
import { useAllUsers } from '@/hooks/use-admin';
import { UserAvatar } from '@/components/admin/user-avatar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
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
import { ArrowLeft, Search, Shield, User } from 'lucide-react';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';

function AllUsersContent() {
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');
  const [includeDeleted, setIncludeDeleted] = useState(false);

  // Fetch users
  const { data: usersData, isLoading } = useAllUsers({
    page,
    page_size: 20,
    include_deleted: includeDeleted,
  });

  // Filter users by search term (email) and role
  const filteredUsers = usersData?.items?.filter((user: any) => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = !roleFilter || user.role === roleFilter;
    return matchesSearch && matchesRole;
  }) ?? [];

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
            <h1 className="text-3xl font-bold">All Users</h1>
            <p className="text-muted-foreground mt-1">
              Manage users and view their activity
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter users by role, status, or email</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search by email */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Role filter */}
            <Select
              value={roleFilter ?? 'all'}
              onValueChange={(value) => {
                setRoleFilter(value === 'all' ? undefined : value);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="user">User</SelectItem>
              </SelectContent>
            </Select>

            {/* Include deleted toggle */}
            <div className="flex items-center space-x-2">
              <Switch
                id="include-deleted"
                checked={includeDeleted}
                onCheckedChange={(checked) => {
                  setIncludeDeleted(checked);
                  setPage(1);
                }}
              />
              <Label htmlFor="include-deleted">Include deleted users</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Users</CardTitle>
              <CardDescription>
                {usersData?.total ?? 0} total users
                {roleFilter && ` with role "${roleFilter}"`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No users found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Sessions</TableHead>
                    <TableHead className="text-right">Tasks</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user: any) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <UserAvatar email={user.email} size="md" />
                          <div className="flex flex-col">
                            <span className="font-medium">{user.email}</span>
                            <span className="text-xs text-muted-foreground">
                              ID: {user.id.substring(0, 8)}...
                            </span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={user.role === 'admin' ? 'default' : 'outline'}
                          className="gap-1"
                        >
                          {user.role === 'admin' ? (
                            <Shield className="h-3 w-3" />
                          ) : (
                            <User className="h-3 w-3" />
                          )}
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <Badge
                            variant={user.is_active ? 'default' : 'secondary'}
                            className="w-fit"
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                          {user.deleted_at && (
                            <Badge variant="destructive" className="w-fit text-xs">
                              Deleted
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {user.session_count ?? 0}
                          </span>
                          <span className="text-xs text-muted-foreground">sessions</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {user.task_count ?? 0}
                          </span>
                          <span className="text-xs text-muted-foreground">tasks</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-sm">{formatDate(user.created_at)}</span>
                          {user.updated_at && (
                            <span className="text-xs text-muted-foreground">
                              Updated: {formatDate(user.updated_at)}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                        >
                          <Link href={`/admin/sessions?user_id=${user.id}`}>
                            View Sessions
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {usersData && usersData.total_pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {usersData.total_pages}
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
                      onClick={() => setPage((p) => Math.min(usersData.total_pages, p + 1))}
                      disabled={page === usersData.total_pages}
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

export default function AllUsersPage() {
  return (
    <AdminRoute>
      <AllUsersContent />
    </AdminRoute>
  );
}
