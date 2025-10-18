'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Eye, MoreVertical, Edit, Trash2, Share2, Copy } from 'lucide-react';
import { SessionTemplateResponse } from '@/types/api';
import { useDeleteTemplate } from '@/hooks/use-session-templates';
import { format } from 'date-fns';

interface TemplateCardProps {
  template: SessionTemplateResponse;
  onEdit?: (template: SessionTemplateResponse) => void;
  onShare?: (template: SessionTemplateResponse) => void;
}

export function TemplateCard({ template, onEdit, onShare }: TemplateCardProps) {
  const router = useRouter();
  const deleteTemplate = useDeleteTemplate();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this template?')) return;

    setIsDeleting(true);
    try {
      await deleteTemplate.mutateAsync(template.id);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleView = () => {
    router.push(`/session-templates/${template.id}`);
  };

  const handleUseTemplate = () => {
    // Navigate to create session with template ID
    router.push(`/sessions/new?templateId=${template.id}`);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-lg">{template.name}</CardTitle>
            {template.description && (
              <CardDescription className="line-clamp-2">
                {template.description}
              </CardDescription>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleView}>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              {onEdit && (
                <DropdownMenuItem onClick={() => onEdit(template)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
              )}
              {onShare && (
                <DropdownMenuItem onClick={() => onShare(template)}>
                  <Share2 className="mr-2 h-4 w-4" />
                  Sharing Settings
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={handleDelete} disabled={isDeleting}>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Category & Visibility Badges */}
          <div className="flex flex-wrap gap-2">
            {template.category && (
              <Badge variant="secondary">{template.category}</Badge>
            )}
            {template.is_public && (
              <Badge variant="outline">Public</Badge>
            )}
            {template.is_organization_shared && (
              <Badge variant="outline">Organization</Badge>
            )}
          </div>

          {/* Tags */}
          {template.tags && template.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {template.tags.slice(0, 5).map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {template.tags.length > 5 && (
                <Badge variant="outline" className="text-xs">
                  +{template.tags.length - 5} more
                </Badge>
              )}
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Usage Count</p>
              <p className="font-medium">{template.usage_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Version</p>
              <p className="font-medium">{template.version}</p>
            </div>
          </div>

          {/* Last Used */}
          {template.last_used_at && (
            <div className="text-sm text-muted-foreground">
              Last used {format(new Date(template.last_used_at), 'MMM d, yyyy')}
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button onClick={handleUseTemplate} className="flex-1">
          <Copy className="mr-2 h-4 w-4" />
          Use Template
        </Button>
        <Button variant="outline" onClick={handleView}>
          View
        </Button>
      </CardFooter>
    </Card>
  );
}
