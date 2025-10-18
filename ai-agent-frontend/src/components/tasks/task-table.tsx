import Link from 'next/link';
import { TaskResponse } from '@/types/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDate } from '@/lib/utils';
import { Play, Edit, Trash2, ToggleLeft, ToggleRight, Calendar, User } from 'lucide-react';

interface TaskTableProps {
  tasks?: TaskResponse[];
  loading?: boolean;
  onExecute?: (taskId: string) => void;
  onEdit?: (taskId: string) => void;
  onDelete?: (taskId: string) => void;
  onToggle?: (taskId: string, enabled: boolean) => void;
}

export function TaskTable({ tasks, loading, onExecute, onEdit, onDelete, onToggle }: TaskTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div className="text-center py-12 border rounded-md bg-gray-50">
        <p className="text-gray-500">No tasks yet. Create your first task to get started!</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Schedule</TableHead>
            <TableHead>Enabled</TableHead>
            <TableHead className="text-center">Success / Fail</TableHead>
            <TableHead>Last Run</TableHead>
            <TableHead>Next Run</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id} className="hover:bg-gray-50">
              <TableCell>
                <div>
                  <Link
                    href={`/tasks/${task.id}`}
                    className="font-medium hover:underline"
                  >
                    {task.name}
                  </Link>
                  {task.description && (
                    <p className="text-sm text-gray-500 truncate max-w-xs">
                      {task.description}
                    </p>
                  )}
                  {task.tags.length > 0 && (
                    <div className="flex gap-1 mt-1">
                      {task.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {task.tags.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{task.tags.length - 3}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell>
                {task.is_scheduled ? (
                  <div className="flex items-center gap-1 text-sm">
                    <Calendar className="h-3 w-3 text-gray-400" />
                    <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">
                      {task.schedule_cron}
                    </code>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-sm text-gray-400">
                    <User className="h-3 w-3" />
                    <span>Manual</span>
                  </div>
                )}
              </TableCell>
              <TableCell>
                {task.is_scheduled ? (
                  <Badge className={task.schedule_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                    {task.schedule_enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                ) : (
                  <span className="text-sm text-gray-400">-</span>
                )}
              </TableCell>
              <TableCell className="text-center">
                <div className="flex items-center justify-center gap-2">
                  <span className="text-green-600 font-medium">{task.success_count}</span>
                  <span className="text-gray-400">/</span>
                  <span className="text-red-600 font-medium">{task.failure_count}</span>
                </div>
              </TableCell>
              <TableCell className="text-sm text-gray-600">
                {task.last_execution_at ? formatDate(task.last_execution_at) : '-'}
              </TableCell>
              <TableCell className="text-sm text-gray-600">
                {task.next_execution_at ? formatDate(task.next_execution_at) : '-'}
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onExecute?.(task.id)}
                    title="Execute task"
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit?.(task.id)}
                    title="Edit task"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  {task.is_scheduled && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onToggle?.(task.id, !task.schedule_enabled)}
                      title={task.schedule_enabled ? 'Disable schedule' : 'Enable schedule'}
                    >
                      {task.schedule_enabled ? (
                        <ToggleRight className="h-4 w-4 text-green-600" />
                      ) : (
                        <ToggleLeft className="h-4 w-4 text-gray-400" />
                      )}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete?.(task.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    title="Delete task"
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
