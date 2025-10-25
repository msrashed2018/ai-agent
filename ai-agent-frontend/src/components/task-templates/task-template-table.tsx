'use client';

import { TaskTemplateResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Trash2, Edit2, Play, FileText } from 'lucide-react';
import { format } from 'date-fns';

interface TaskTemplateTableProps {
  templates: TaskTemplateResponse[];
  isLoading: boolean;
  onEdit: (template: TaskTemplateResponse) => void;
  onDelete: (templateId: string) => void;
  onCreateTask?: (template: TaskTemplateResponse) => void;
}

export function TaskTemplateTable({
  templates,
  isLoading,
  onEdit,
  onDelete,
  onCreateTask,
}: TaskTemplateTableProps) {
  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading task templates...</div>;
  }

  if (!templates || templates.length === 0) {
    return <div className="p-8 text-center text-gray-500">No task templates found. Create one to get started.</div>;
  }

  return (
    <div className="space-y-4">
      {/* Grid view for better visual hierarchy */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className="rounded-lg border border-gray-200 bg-white p-5 hover:shadow-lg hover:border-gray-300 transition-all duration-200"
          >
            {/* Header with icon and name */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start gap-3 flex-1">
                {template.icon && (
                  <div className="text-2xl flex-shrink-0 mt-1">{template.icon}</div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate text-base">
                    {template.name}
                  </h3>
                  {template.category && (
                    <p className="text-xs text-gray-500 mt-1">Category: {template.category}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Description */}
            {template.description && (
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                {template.description}
              </p>
            )}

            {/* Status badges */}
            <div className="flex gap-2 mb-3 flex-wrap">
              {template.is_active ? (
                <Badge className="bg-green-100 text-green-800 border-green-300">
                  ✓ Active
                </Badge>
              ) : (
                <Badge variant="secondary" className="bg-gray-100 text-gray-800">
                  ✗ Inactive
                </Badge>
              )}
              {template.is_public && (
                <Badge className="bg-blue-100 text-blue-800 border-blue-300">
                  🌐 Public
                </Badge>
              )}
            </div>

            {/* Tags */}
            {template.tags && template.tags.length > 0 && (
              <div className="mb-3">
                <div className="flex flex-wrap gap-1">
                  {template.tags.slice(0, 3).map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="text-xs bg-purple-100 text-purple-800"
                    >
                      #{tag}
                    </Badge>
                  ))}
                  {template.tags.length > 3 && (
                    <span className="text-xs text-gray-500 font-medium">
                      +{template.tags.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="flex items-center justify-between py-3 border-t border-gray-100 text-sm">
              <div className="text-gray-600">
                <span className="font-medium text-gray-900">{template.usage_count}</span> uses
              </div>
              <div className="text-gray-500 text-xs">
                {format(new Date(template.created_at), 'MMM d, yyyy')}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-3 border-t border-gray-100">
              {onCreateTask && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCreateTask(template)}
                  className="flex-1 text-green-700 hover:bg-green-50 border-green-200"
                  title="Create task from this template"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Create Task
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(template)}
                className="flex-1 text-blue-700 hover:bg-blue-50 border-blue-200"
                title="Edit template"
              >
                <Edit2 className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete(template.id)}
                className="flex-1 text-red-700 hover:bg-red-50 border-red-200"
                title="Delete template"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Table view fallback for mobile - optional */}
      {templates.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">
            <FileText className="h-12 w-12 mx-auto opacity-50" />
          </div>
          <p className="text-gray-600 font-medium">No task templates found</p>
          <p className="text-sm text-gray-500 mt-1">Create your first template to get started</p>
        </div>
      )}
    </div>
  );
}
