'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useTask, useTaskExecutions, useDeleteTask, useUpdateTask } from '@/hooks/use-tasks';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ExecutionTable } from '@/components/tasks/execution-table';
import { ExecuteTaskDialog } from '@/components/tasks/execute-task-dialog';
import { ArrowLeft, Play, Edit, Trash2, Calendar, ToggleLeft, ToggleRight, FileText } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.taskId as string;

  const [showExecuteDialog, setShowExecuteDialog] = useState(false);
  const { data: task, isLoading: taskLoading } = useTask(taskId);
  const { data: executions, isLoading: executionsLoading } = useTaskExecutions(taskId, { page_size: 10 });
  const deleteTask = useDeleteTask();
  const updateTask = useUpdateTask(taskId);

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
      await deleteTask.mutateAsync(taskId);
      router.push('/tasks');
    }
  };

  const handleToggleSchedule = async () => {
    if (task) {
      await updateTask.mutateAsync({ schedule_enabled: !task.schedule_enabled });
    }
  };

  if (taskLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
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

  if (!task) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">Task not found</p>
            <Link href="/tasks" className="mt-4 inline-block">
              <Button variant="outline">Back to Tasks</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalExecutions = task.success_count + task.failure_count;
  const successRate = totalExecutions > 0 ? ((task.success_count / totalExecutions) * 100).toFixed(1) : '0';

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-6">
        <Link href="/tasks">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Tasks
          </Button>
        </Link>
      </div>

      {/* Task Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">{task.name}</h1>
            {task.description && (
              <p className="text-gray-600">{task.description}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowExecuteDialog(true)}>
              <Play className="mr-2 h-4 w-4" />
              Execute
            </Button>
            <Link href={`/tasks/${taskId}/edit`}>
              <Button variant="outline">
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            </Link>
            {task.is_scheduled && (
              <Button
                variant="outline"
                onClick={handleToggleSchedule}
                disabled={updateTask.isPending}
              >
                {task.schedule_enabled ? (
                  <>
                    <ToggleRight className="mr-2 h-4 w-4 text-green-600" />
                    Disable
                  </>
                ) : (
                  <>
                    <ToggleLeft className="mr-2 h-4 w-4 text-gray-400" />
                    Enable
                  </>
                )}
              </Button>
            )}
            <Button variant="outline" onClick={handleDelete} className="text-red-600 hover:bg-red-50">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>

        {task.tags.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {task.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Total Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalExecutions}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">{successRate}%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Last Run</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{task.last_execution_at ? formatDate(task.last_execution_at) : 'Never'}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Next Run</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{task.next_execution_at ? formatDate(task.next_execution_at) : 'Not scheduled'}</p>
          </CardContent>
        </Card>
      </div>

      {/* Task Configuration */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Task Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Schedule */}
          {task.is_scheduled && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Schedule
              </h4>
              <div className="flex items-center gap-2">
                <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
                  {task.schedule_cron}
                </code>
                <Badge className={task.schedule_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                  {task.schedule_enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
            </div>
          )}

          {/* Report Generation */}
          {task.generate_report && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Report Generation
              </h4>
              <p className="text-sm text-gray-600">
                Format: <span className="font-medium">{task.report_format?.toUpperCase()}</span>
              </p>
            </div>
          )}

          {/* Template */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Prompt Template</h4>
            <pre className="bg-gray-50 p-3 rounded-md text-sm overflow-x-auto border">
              {task.prompt_template}
            </pre>
          </div>

          {/* Variables */}
          {Object.keys(task.template_variables).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Template Variables</h4>
              <div className="space-y-2">
                {Object.entries(task.template_variables).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    <code className="bg-gray-100 px-2 py-1 rounded font-mono">{key}</code>
                    <span className="text-gray-400">=</span>
                    <span className="text-gray-600">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution History */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
          <CardDescription>Recent executions for this task</CardDescription>
        </CardHeader>
        <CardContent>
          <ExecutionTable
            executions={executions?.items}
            loading={executionsLoading}
          />
          {executions && executions.total > 10 && (
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-500">
                Showing 10 of {executions.total} executions
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execute Dialog */}
      {showExecuteDialog && (
        <ExecuteTaskDialog
          task={task}
          open={showExecuteDialog}
          onClose={() => setShowExecuteDialog(false)}
        />
      )}
    </div>
  );
}
