'use client';

import { useState } from 'react';
import { ToolGroupResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Trash2, Edit2 } from 'lucide-react';
import { format } from 'date-fns';

interface ToolGroupTableProps {
  toolGroups: ToolGroupResponse[];
  isLoading: boolean;
  onEdit: (toolGroup: ToolGroupResponse) => void;
  onDelete: (toolGroupId: string) => void;
}

export function ToolGroupTable({
  toolGroups,
  isLoading,
  onEdit,
  onDelete,
}: ToolGroupTableProps) {
  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading tool groups...</div>;
  }

  if (!toolGroups || toolGroups.length === 0) {
    return <div className="p-8 text-center text-gray-500">No tool groups found. Create one to get started.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="border-b bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left font-semibold">Name</th>
            <th className="px-6 py-3 text-left font-semibold">Description</th>
            <th className="px-6 py-3 text-left font-semibold">Allowed Tools</th>
            <th className="px-6 py-3 text-left font-semibold">Disallowed Tools</th>
            <th className="px-6 py-3 text-left font-semibold">Created</th>
            <th className="px-6 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {toolGroups.map((group) => (
            <tr key={group.id} className="hover:bg-gray-50">
              <td className="px-6 py-3 font-medium">
                <div className="flex items-center gap-2">
                  {group.name}
                  {group.is_public && <Badge variant="secondary">Public</Badge>}
                </div>
              </td>
              <td className="px-6 py-3 text-gray-600">
                {group.description ? (
                  <span className="truncate">{group.description}</span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="px-6 py-3">
                <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                  {group.allowed_tools?.length || 0}
                </span>
              </td>
              <td className="px-6 py-3">
                <span className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">
                  {group.disallowed_tools?.length || 0}
                </span>
              </td>
              <td className="px-6 py-3 text-gray-600">
                {format(new Date(group.created_at), 'MMM d, yyyy')}
              </td>
              <td className="px-6 py-3 text-right">
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(group)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(group.id)}
                    className="h-8 w-8 p-0 text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
