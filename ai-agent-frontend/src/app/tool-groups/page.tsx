'use client';

import { useState } from 'react';
import { useToolGroups, useCreateToolGroup, useDeleteToolGroup, useUpdateToolGroup } from '@/hooks/use-tool-groups';
import { ToolGroupTable, ToolGroupForm, ToolGroupSelector } from '@/components/tool-groups';
import { Button } from '@/components/ui/button';
import { Plus, ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import type { ToolGroupCreateRequest, ToolGroupResponse } from '@/types/api';

export default function ToolGroupsPage() {
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data, isLoading } = useToolGroups();
  const createMutation = useCreateToolGroup();
  const updateMutation = useUpdateToolGroup(editingId || '');
  const deleteMutation = useDeleteToolGroup();

  const toolGroups = data?.items || [];
  const editingGroup = editingId ? toolGroups.find((g) => g.id === editingId) : null;

  const handleCreateOrUpdate = async (formData: ToolGroupCreateRequest) => {
    if (editingId) {
      await updateMutation.mutateAsync(formData);
      setEditingId(null);
    } else {
      await createMutation.mutateAsync(formData);
      setIsCreating(false);
    }
  };

  const handleDelete = (toolGroupId: string) => {
    if (confirm('Are you sure you want to delete this tool group?')) {
      deleteMutation.mutate(toolGroupId);
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingId(null);
  };

  const handleEdit = (group: ToolGroupResponse) => {
    setEditingId(group.id);
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
                <h1 className="text-3xl font-bold text-gray-900">Tool Groups</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Organize and manage reusable tool configurations
                </p>
              </div>
            </div>
            {!isCreating && !editingId && (
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Tool Group
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
              {editingId ? 'Edit Tool Group' : 'Create New Tool Group'}
            </h2>
            <ToolGroupForm
              initialData={editingGroup || null}
              isSubmitting={isSubmitting}
              onSubmit={handleCreateOrUpdate}
              onCancel={handleCancel}
            />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border bg-white p-4">
                <p className="text-sm text-gray-600">Total Tool Groups</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {toolGroups.length}
                </p>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <p className="text-sm text-gray-600">Active</p>
                <p className="mt-2 text-3xl font-bold text-blue-600">
                  {toolGroups.filter((g) => g.is_active).length}
                </p>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <p className="text-sm text-gray-600">Public</p>
                <p className="mt-2 text-3xl font-bold text-green-600">
                  {toolGroups.filter((g) => g.is_public).length}
                </p>
              </div>
            </div>

            {/* Tool Groups Table */}
            <ToolGroupTable
              toolGroups={toolGroups}
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
