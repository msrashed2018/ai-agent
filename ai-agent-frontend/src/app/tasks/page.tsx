'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTasks, useDeleteTask, useUpdateTask } from '@/hooks/use-tasks';
import { TaskResponse } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TaskTable } from '@/components/tasks/task-table';
import { ExecuteTaskDialog } from '@/components/tasks/execute-task-dialog';
import { Plus, Search, Filter } from 'lucide-react';

export default function TasksPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterScheduled, setFilterScheduled] = useState<'all' | 'scheduled' | 'manual'>('all');
  const [filterEnabled, setFilterEnabled] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [executeTask, setExecuteTask] = useState<TaskResponse | null>(null);

  // Build query params
  const queryParams = {
    is_scheduled: filterScheduled === 'all' ? undefined : filterScheduled === 'scheduled',
  };

  const { data, isLoading } = useTasks(queryParams);
  const deleteTask = useDeleteTask();
  const updateTask = useUpdateTask('');

  // Client-side filtering for search and enabled status
  const filteredTasks = data?.items?.filter((task) => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesName = task.name.toLowerCase().includes(query);
      const matchesDescription = task.description?.toLowerCase().includes(query);
      const matchesTags = task.tags.some((tag) => tag.toLowerCase().includes(query));
      if (!matchesName && !matchesDescription && !matchesTags) {
        return false;
      }
    }

    // Enabled filter
    if (filterEnabled !== 'all') {
      if (filterEnabled === 'enabled' && !task.schedule_enabled) return false;
      if (filterEnabled === 'disabled' && task.schedule_enabled) return false;
    }

    return true;
  });

  const handleExecute = (taskId: string) => {
    const task = data?.items.find((t) => t.id === taskId);
    if (task) {
      setExecuteTask(task);
    }
  };

  const handleEdit = (taskId: string) => {
    router.push(`/tasks/${taskId}/edit`);
  };

  const handleDelete = async (taskId: string) => {
    if (confirm('Are you sure you want to delete this task?')) {
      await deleteTask.mutateAsync(taskId);
    }
  };

  const handleToggle = async (taskId: string, enabled: boolean) => {
    await updateTask.mutateAsync({ schedule_enabled: enabled });
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Tasks</h1>
          <p className="text-gray-600 mt-1">Manage and execute automated tasks</p>
        </div>
        <Link href="/tasks/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Task
          </Button>
        </Link>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search tasks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <Select value={filterScheduled} onValueChange={(value: any) => setFilterScheduled(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tasks</SelectItem>
                  <SelectItem value="scheduled">Scheduled Only</SelectItem>
                  <SelectItem value="manual">Manual Only</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={filterEnabled} onValueChange={(value: any) => setFilterEnabled(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="enabled">Enabled</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            {filteredTasks ? `${filteredTasks.length} Tasks` : 'Loading...'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <TaskTable
            tasks={filteredTasks}
            loading={isLoading}
            onExecute={handleExecute}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onToggle={handleToggle}
          />
        </CardContent>
      </Card>

      {executeTask && (
        <ExecuteTaskDialog
          task={executeTask}
          open={!!executeTask}
          onClose={() => setExecuteTask(null)}
        />
      )}
    </div>
  );
}
