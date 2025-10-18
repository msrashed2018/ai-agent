'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { SessionTemplateResponse } from '@/types/api';
import { Eye, Edit, Trash2, Share2, Globe, Building2 } from 'lucide-react';
import { useState } from 'react';

interface TemplateTableProps {
  templates?: SessionTemplateResponse[];
  loading?: boolean;
  onView?: (templateId: string) => void;
  onEdit?: (templateId: string) => void;
  onDelete?: (templateId: string) => void;
  onShare?: (template: SessionTemplateResponse) => void;
}

type SortField = 'name' | 'category' | 'usage_count';
type SortDirection = 'asc' | 'desc';

export function TemplateTable({
  templates,
  loading,
  onView,
  onEdit,
  onDelete,
  onShare,
}: TemplateTableProps) {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedTemplates = React.useMemo(() => {
    if (!templates) return [];

    return [...templates].sort((a, b) => {
      let aVal: string | number = '';
      let bVal: string | number = '';

      switch (sortField) {
        case 'name':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case 'category':
          aVal = (a.category || '').toLowerCase();
          bVal = (b.category || '').toLowerCase();
          break;
        case 'usage_count':
          aVal = a.usage_count;
          bVal = b.usage_count;
          break;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [templates, sortField, sortDirection]);

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <div className="text-center py-12 border rounded-md bg-gray-50">
        <p className="text-gray-500">No templates found. Create your first template to get started!</p>
      </div>
    );
  }

  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <TableHead
      className="cursor-pointer hover:bg-gray-50 select-none"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field && (
          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </TableHead>
  );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader field="name">Name</SortableHeader>
            <SortableHeader field="category">Category</SortableHeader>
            <TableHead>Tags</TableHead>
            <SortableHeader field="usage_count">Usage Count</SortableHeader>
            <TableHead>Visibility</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedTemplates.map((template) => (
            <TableRow key={template.id} className="hover:bg-gray-50">
              <TableCell>
                <div>
                  <Link
                    href={`/session-templates/${template.id}`}
                    className="font-medium hover:underline"
                  >
                    {template.name}
                  </Link>
                  {template.description && (
                    <p className="text-sm text-gray-500 truncate max-w-xs">
                      {template.description}
                    </p>
                  )}
                </div>
              </TableCell>
              <TableCell>
                {template.category ? (
                  <Badge variant="secondary" className="capitalize">
                    {template.category}
                  </Badge>
                ) : (
                  <span className="text-sm text-gray-400">-</span>
                )}
              </TableCell>
              <TableCell>
                {template.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {template.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {template.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{template.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">-</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-sm font-medium">{template.usage_count}</span>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {template.is_public && (
                    <Badge className="bg-blue-100 text-blue-800 flex items-center gap-1">
                      <Globe className="h-3 w-3" />
                      Public
                    </Badge>
                  )}
                  {template.is_organization_shared && (
                    <Badge className="bg-purple-100 text-purple-800 flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      Org
                    </Badge>
                  )}
                  {!template.is_public && !template.is_organization_shared && (
                    <Badge variant="secondary">Private</Badge>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onView?.(template.id)}
                    title="View template"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit?.(template.id)}
                    title="Edit template"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onShare?.(template)}
                    title="Sharing settings"
                  >
                    <Share2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete?.(template.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    title="Delete template"
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
