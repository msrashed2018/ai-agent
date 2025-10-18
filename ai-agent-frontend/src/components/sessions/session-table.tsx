'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, formatCurrency, getStatusColor } from '@/lib/utils';
import { SessionResponse } from '@/types/api';
import { Eye, MessageSquare, Pause, Play, Trash2 } from 'lucide-react';

interface SessionTableProps {
  sessions: SessionResponse[];
  onPause?: (sessionId: string) => void;
  onResume?: (sessionId: string) => void;
  onDelete?: (sessionId: string) => void;
  isLoading?: boolean;
}

export function SessionTable({
  sessions,
  onPause,
  onResume,
  onDelete,
  isLoading = false,
}: SessionTableProps) {
  const router = useRouter();

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading sessions...</div>;
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No sessions found. Create your first session to get started.
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
            <TableHead>Model</TableHead>
            <TableHead className="text-right">Messages</TableHead>
            <TableHead className="text-right">Tool Calls</TableHead>
            <TableHead className="text-right">Cost</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id}>
              <TableCell className="font-medium">
                <Link
                  href={`/sessions/${session.id}`}
                  className="text-blue-600 hover:underline"
                >
                  {session.name || `Session ${session.id.substring(0, 8)}`}
                </Link>
                {session.description && (
                  <p className="text-xs text-gray-500 mt-1">{session.description}</p>
                )}
              </TableCell>
              <TableCell>
                <Badge className={getStatusColor(session.status)}>{session.status}</Badge>
              </TableCell>
              <TableCell>
                <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                  {session.sdk_options?.model || 'N/A'}
                </code>
              </TableCell>
              <TableCell className="text-right">{session.message_count}</TableCell>
              <TableCell className="text-right">{session.tool_call_count}</TableCell>
              <TableCell className="text-right">
                {session.total_cost_usd ? formatCurrency(session.total_cost_usd) : '-'}
              </TableCell>
              <TableCell>{formatDate(session.created_at)}</TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/sessions/${session.id}`)}
                    title="View Details"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/sessions/${session.id}/query`)}
                    title="Query Session"
                    disabled={session.status === 'completed' || session.status === 'failed'}
                  >
                    <MessageSquare className="h-4 w-4" />
                  </Button>
                  {session.status === 'active' ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onPause?.(session.id)}
                      title="Pause Session"
                    >
                      <Pause className="h-4 w-4" />
                    </Button>
                  ) : session.status === 'paused' ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onResume?.(session.id)}
                      title="Resume Session"
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                  ) : null}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete?.(session.id)}
                    title="Delete Session"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
