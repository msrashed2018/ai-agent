'use client';

import * as React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, formatCurrency, getStatusColor } from '@/lib/utils';
import { SessionResponse } from '@/types/api';
import { MessageSquare, Eye, Pause, Play, Download } from 'lucide-react';

interface SessionCardProps {
  session: SessionResponse;
  onPause?: (sessionId: string) => void;
  onResume?: (sessionId: string) => void;
  onDownload?: (sessionId: string) => void;
}

export function SessionCard({ session, onPause, onResume, onDownload }: SessionCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle>
              <Link href={`/sessions/${session.id}`} className="hover:underline">
                {session.name || `Session ${session.id.substring(0, 8)}`}
              </Link>
            </CardTitle>
            {session.description && (
              <CardDescription className="mt-2">{session.description}</CardDescription>
            )}
          </div>
          <Badge className={getStatusColor(session.status)}>{session.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Messages</p>
              <p className="font-semibold">{session.message_count}</p>
            </div>
            <div>
              <p className="text-gray-500">Tool Calls</p>
              <p className="font-semibold">{session.tool_call_count}</p>
            </div>
            <div>
              <p className="text-gray-500">Cost</p>
              <p className="font-semibold">
                {session.total_cost_usd ? formatCurrency(session.total_cost_usd) : '-'}
              </p>
            </div>
          </div>

          {/* Model Info */}
          <div className="text-sm">
            <p className="text-gray-500">Model</p>
            <code className="bg-gray-100 px-2 py-1 rounded text-xs">
              {session.sdk_options?.model || 'N/A'}
            </code>
          </div>

          {/* Timestamps */}
          <div className="text-sm space-y-1">
            <p className="text-gray-500">Created: {formatDate(session.created_at)}</p>
            {session.completed_at && (
              <p className="text-gray-500">Completed: {formatDate(session.completed_at)}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild className="flex-1">
              <Link href={`/sessions/${session.id}`}>
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              asChild
              className="flex-1"
              disabled={session.status === 'completed' || session.status === 'failed'}
            >
              <Link href={`/sessions/${session.id}/query`}>
                <MessageSquare className="h-4 w-4 mr-2" />
                Query
              </Link>
            </Button>
            {session.status === 'active' && (
              <Button variant="outline" size="sm" onClick={() => onPause?.(session.id)}>
                <Pause className="h-4 w-4 mr-2" />
                Pause
              </Button>
            )}
            {session.status === 'paused' && (
              <Button variant="outline" size="sm" onClick={() => onResume?.(session.id)}>
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
            )}
            {session.working_directory && (
              <Button variant="outline" size="sm" onClick={() => onDownload?.(session.id)}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
