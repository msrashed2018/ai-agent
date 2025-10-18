'use client';

import { useRouter } from 'next/navigation';
import { useCreateTask } from '@/hooks/use-tasks';
import { TaskCreateRequest, TaskUpdateRequest } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TaskForm } from '@/components/tasks/task-form';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewTaskPage() {
  const router = useRouter();
  const createTask = useCreateTask();

  const handleSubmit = async (data: TaskCreateRequest | TaskUpdateRequest) => {
    await createTask.mutateAsync(data as TaskCreateRequest);
    router.push('/tasks');
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <Link href="/tasks">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Tasks
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create New Task</CardTitle>
          <CardDescription>
            Define a new automated task with prompt templates and scheduling options
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TaskForm
            onSubmit={handleSubmit}
            isSubmitting={createTask.isPending}
            submitLabel="Create Task"
          />
        </CardContent>
      </Card>
    </div>
  );
}
