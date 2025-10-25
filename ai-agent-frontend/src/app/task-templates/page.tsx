'use client';

import { useState } from 'react';
import {
  useTaskTemplates,
  useCreateTaskTemplate,
  useDeleteTaskTemplate,
  useUpdateTaskTemplate,
  useTaskTemplateStats,
} from '@/hooks/use-task-templates';
import { TaskTemplateTable, TaskTemplateForm } from '@/components/task-templates';
import { Button } from '@/components/ui/button';
import { Plus, ChevronLeft, FileText, CheckCircle, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import type { TaskTemplateCreateRequest, TaskTemplateResponse } from '@/types/api';

export default function TaskTemplatesPage() {
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data, isLoading } = useTaskTemplates();
  const { data: stats, isLoading: statsLoading } = useTaskTemplateStats();
  const createMutation = useCreateTaskTemplate();
  const updateMutation = useUpdateTaskTemplate(editingId || '');
  const deleteMutation = useDeleteTaskTemplate();

  const templates = data?.items || [];
  const editingTemplate = editingId ? templates.find((t) => t.id === editingId) : null;

  const handleCreateOrUpdate = async (formData: TaskTemplateCreateRequest) => {
    if (editingId) {
      await updateMutation.mutateAsync(formData);
      setEditingId(null);
    } else {
      await createMutation.mutateAsync(formData);
      setIsCreating(false);
    }
  };

  const handleDelete = (templateId: string) => {
    if (confirm('Are you sure you want to delete this task template?')) {
      deleteMutation.mutate(templateId);
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingId(null);
  };

  const handleEdit = (template: TaskTemplateResponse) => {
    setEditingId(template.id);
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                <ChevronLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Task Templates</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Create and manage reusable task templates with custom prompts
                </p>
              </div>
            </div>
            {!isCreating && !editingId && (
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Task Template
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {isCreating || editingId ? (
          <div className="rounded-lg border bg-white p-8">
            <h2 className="mb-6 text-2xl font-semibold">
              {editingId ? 'Edit Task Template' : 'Create New Task Template'}
            </h2>
            <TaskTemplateForm
              initialData={editingTemplate || null}
              isSubmitting={isSubmitting}
              onSubmit={handleCreateOrUpdate}
              onCancel={handleCancel}
            />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <FileText className="h-4 w-4" />
                  <span>Total Templates</span>
                </div>
                <p className="text-3xl font-bold text-gray-900">
                  {statsLoading ? '...' : stats?.total_templates || 0}
                </p>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>Active</span>
                </div>
                <p className="text-3xl font-bold text-blue-600">
                  {statsLoading ? '...' : stats?.active_templates || 0}
                </p>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Categories</span>
                </div>
                <p className="text-3xl font-bold text-green-600">
                  {statsLoading ? '...' : stats?.categories?.length || 0}
                </p>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <span>Most Used</span>
                </div>
                <p className="text-3xl font-bold text-purple-600">
                  {statsLoading ? '...' : stats?.most_used?.[0]?.usage_count || 0}
                </p>
              </div>
            </div>

            {/* Categories Overview */}
            {stats && stats.categories && Object.keys(stats.categories).length > 0 && (
              <div className="rounded-lg border bg-white p-6">
                <h3 className="text-lg font-semibold mb-4">Categories</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.categories).map(([category, count]) => (
                    <div
                      key={category}
                      className="inline-flex items-center rounded-full bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700"
                    >
                      {category}
                      <span className="ml-2 rounded-full bg-gray-200 px-2 py-0.5 text-xs">
                        {count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Task Templates Table */}
            <TaskTemplateTable
              templates={templates}
              isLoading={isLoading}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          </div>
        )}
      </div>
    </div>
  );
}
