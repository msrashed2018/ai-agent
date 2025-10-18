'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useTaskExecution, useExecuteTask } from '@/hooks/use-tasks';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, RefreshCw, CheckCircle2, XCircle, Clock, Loader2, ExternalLink } from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';

export default function ExecutionDetailPage() {
  const params = useParams();
  const executionId = params.executionId as string;

  const { data: execution, isLoading } = useTaskExecution(executionId);
  const executeTask = useExecuteTask(execution?.task_id || '');

  const handleRerun = async () => {
    if (execution) {
      await executeTask.mutateAsync({ variables: execution.variables });
    }
  };

  const getStatusIcon = () => {
    if (!execution) return null;

    switch (execution.status) {
      case 'completed':
        return <CheckCircle2 className="h-6 w-6 text-green-600" />;
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-600" />;
      case 'running':
        return <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock className="h-6 w-6 text-gray-400" />;
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

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <Skeleton className="h-8 w-64 mb-6" />
        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48 mb-2" />
              <Skeleton className="h-4 w-96" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">Execution not found</p>
            <Link href="/tasks" className="mt-4 inline-block">
              <Button variant="outline">Back to Tasks</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const duration = execution.completed_at
    ? formatDuration(execution.started_at, execution.completed_at)
    : null;

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <Link href={`/tasks/${execution.task_id}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Task
          </Button>
        </Link>
      </div>

      {/* Execution Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h1 className="text-2xl font-bold">Task Execution</h1>
              <p className="text-gray-600 text-sm mt-1">ID: {execution.id}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleRerun}
              disabled={executeTask.isPending}
              variant="outline"
            >
              {executeTask.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Re-run
            </Button>
          </div>
        </div>
      </div>

      {/* Status Alert */}
      {execution.status === 'failed' && execution.error_message && (
        <Alert variant="destructive" className="mb-6">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Execution Failed:</strong> {execution.error_message}
          </AlertDescription>
        </Alert>
      )}

      {execution.status === 'running' && (
        <Alert className="mb-6 bg-blue-50 border-blue-200">
          <Loader2 className="h-4 w-4 animate-spin" />
          <AlertDescription>
            <strong>Execution in Progress:</strong> This task is currently running. The page will auto-refresh.
          </AlertDescription>
        </Alert>
      )}

      {/* Execution Details */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Execution Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Status</p>
              <Badge className={getStatusColor(execution.status)}>
                {execution.status}
              </Badge>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700">Duration</p>
              <p className="text-sm text-gray-600">
                {duration || (execution.status === 'running' ? 'Running...' : 'Not completed')}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700">Started At</p>
              <p className="text-sm text-gray-600">{formatDate(execution.started_at)}</p>
            </div>

            {execution.completed_at && (
              <div>
                <p className="text-sm font-medium text-gray-700">Completed At</p>
                <p className="text-sm text-gray-600">{formatDate(execution.completed_at)}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Variables Used */}
      {Object.keys(execution.variables).length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Variables Used</CardTitle>
            <CardDescription>Variables passed to this execution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(execution.variables).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2 text-sm">
                  <code className="bg-gray-100 px-2 py-1 rounded font-mono">{key}</code>
                  <span className="text-gray-400">=</span>
                  <span className="text-gray-600 font-mono">{String(value)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Links */}
      <Card>
        <CardHeader>
          <CardTitle>Related Resources</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Link
            href={`/tasks/${execution.task_id}`}
            className="flex items-center gap-2 text-blue-600 hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            View Task Definition
          </Link>

          <Link
            href={`/sessions/${execution.session_id}`}
            className="flex items-center gap-2 text-blue-600 hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            View Agent Session
          </Link>

          {execution.report_id && (
            <Link
              href={`/reports/${execution.report_id}`}
              className="flex items-center gap-2 text-blue-600 hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              View Generated Report
            </Link>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
