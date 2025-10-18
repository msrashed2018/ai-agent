import Link from 'next/link';
import { TaskExecutionResponse } from '@/types/api';
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
import { formatDate, formatDuration } from '@/lib/utils';
import { CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';

interface ExecutionTableProps {
  executions?: TaskExecutionResponse[];
  loading?: boolean;
}

export function ExecutionTable({ executions, loading }: ExecutionTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="text-center py-12 border rounded-md bg-gray-50">
        <p className="text-gray-500">No executions yet</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Session</TableHead>
            <TableHead>Report</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {executions.map((execution) => {
            const duration = execution.completed_at
              ? formatDuration(execution.started_at, execution.completed_at)
              : null;

            return (
              <TableRow key={execution.id} className="cursor-pointer hover:bg-gray-50">
                <TableCell>
                  <Link href={`/tasks/executions/${execution.id}`} className="flex items-center gap-2">
                    {getStatusIcon(execution.status)}
                    <Badge className={getStatusColor(execution.status)}>
                      {execution.status}
                    </Badge>
                  </Link>
                </TableCell>
                <TableCell className="text-sm text-gray-600">
                  {formatDate(execution.started_at)}
                </TableCell>
                <TableCell className="text-sm">
                  {duration || (execution.status === 'running' ? 'Running...' : '-')}
                </TableCell>
                <TableCell>
                  <Link
                    href={`/sessions/${execution.session_id}`}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View Session
                  </Link>
                </TableCell>
                <TableCell>
                  {execution.report_id ? (
                    <Link
                      href={`/reports/${execution.report_id}`}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      View Report
                    </Link>
                  ) : (
                    <span className="text-sm text-gray-400">-</span>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
