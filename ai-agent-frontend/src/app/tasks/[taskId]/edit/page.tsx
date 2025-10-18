'use client';

import { useRouter, useParams } from 'next/navigation';
import { useTask, useUpdateTask } from '@/hooks/use-tasks';
import { TaskUpdateRequest } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { TaskForm } from '@/components/tasks/task-form';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function EditTaskPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.taskId as string;

  const { data: task, isLoading } = useTask(taskId);
  const updateTask = useUpdateTask(taskId);

  const handleSubmit = async (data: TaskUpdateRequest) => {
    await updateTask.mutateAsync(data);
    router.push(`/tasks/${taskId}`);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <Skeleton className="h-8 w-64 mb-6" />
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
    );
  }

  if (!task) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
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

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <Link href={`/tasks/${taskId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Task
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Edit Task: {task.name}</CardTitle>
          <CardDescription>
            Update task configuration and settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TaskForm
            task={task}
            onSubmit={handleSubmit}
            isSubmitting={updateTask.isPending}
            submitLabel="Update Task"
          />
        </CardContent>
      </Card>
    </div>
  );
}
