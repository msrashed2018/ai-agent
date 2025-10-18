import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useExecuteTask } from '@/hooks/use-tasks';
import { TaskResponse } from '@/types/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

interface ExecuteTaskDialogProps {
  task: TaskResponse;
  open: boolean;
  onClose: () => void;
}

export function ExecuteTaskDialog({ task, open, onClose }: ExecuteTaskDialogProps) {
  const router = useRouter();
  const executeTask = useExecuteTask(task.id);
  const [variables, setVariables] = useState<Record<string, string>>(task.template_variables || {});
  const [executionId, setExecutionId] = useState<string | null>(null);

  const handleExecute = async () => {
    try {
      const result = await executeTask.mutateAsync({ variables });
      setExecutionId(result.id);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleClose = () => {
    setVariables(task.template_variables || {});
    setExecutionId(null);
    onClose();
  };

  const handleViewExecution = () => {
    if (executionId) {
      router.push(`/tasks/executions/${executionId}`);
      handleClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Execute Task: {task.name}</DialogTitle>
          <DialogDescription>
            {task.description || 'Configure variables and execute the task'}
          </DialogDescription>
        </DialogHeader>

        {executionId ? (
          <div className="py-6">
            <Alert className="bg-green-50 border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-green-800">Task execution started successfully!</p>
                  <p className="text-sm text-green-700 mt-1">Execution ID: {executionId}</p>
                </div>
              </div>
            </Alert>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.keys(task.template_variables || {}).length > 0 ? (
              <div className="space-y-3">
                <Label className="text-sm font-medium">Template Variables</Label>
                {Object.entries(task.template_variables || {}).map(([key, defaultValue]) => (
                  <div key={key} className="space-y-1">
                    <Label htmlFor={key} className="text-sm">
                      {key}
                    </Label>
                    <Input
                      id={key}
                      value={variables[key] || ''}
                      onChange={(e) =>
                        setVariables((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      placeholder={`Default: ${defaultValue}`}
                      className="font-mono text-sm"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                This task has no template variables. Click execute to run with the default prompt.
              </p>
            )}
          </div>
        )}

        <DialogFooter>
          {executionId ? (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button onClick={handleViewExecution}>View Execution</Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={handleClose} disabled={executeTask.isPending}>
                Cancel
              </Button>
              <Button onClick={handleExecute} disabled={executeTask.isPending}>
                {executeTask.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Execute
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
