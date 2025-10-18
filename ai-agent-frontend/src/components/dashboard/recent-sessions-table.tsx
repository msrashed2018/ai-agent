import Link from 'next/link';
import { SessionResponse } from '@/types/api';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDate, getStatusColor } from '@/lib/utils';

interface RecentSessionsTableProps {
  sessions?: SessionResponse[];
  loading?: boolean;
}

export function RecentSessionsTable({ sessions, loading }: RecentSessionsTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center space-x-4">
            <Skeleton className="h-12 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No sessions yet. Create your first session to get started!</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Messages</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Cost</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id} className="cursor-pointer hover:bg-gray-50">
              <TableCell className="font-medium">
                <Link href={`/sessions/${session.id}`} className="hover:underline">
                  {session.name || 'Unnamed Session'}
                </Link>
              </TableCell>
              <TableCell>
                <Badge className={getStatusColor(session.status)}>
                  {session.status}
                </Badge>
              </TableCell>
              <TableCell>{session.message_count}</TableCell>
              <TableCell className="text-sm text-gray-600">
                {formatDate(session.created_at)}
              </TableCell>
              <TableCell className="text-right">
                {session.total_cost_usd !== null && session.total_cost_usd !== undefined
                  ? `$${session.total_cost_usd.toFixed(4)}`
                  : '-'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
