'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSessionTemplate, useDeleteTemplate } from '@/hooks/use-session-templates';
import { AppLayout } from '@/components/layout/app-layout';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Copy,
  Share2,
  Calendar,
  Tag,
  Folder,
  Settings,
  Globe,
  Building,
} from 'lucide-react';
import { format } from 'date-fns';
import { useState } from 'react';

export default function TemplateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.templateId as string;
  const [isDeleting, setIsDeleting] = useState(false);

  const { data: template, isLoading } = useSessionTemplate(templateId);
  const deleteTemplate = useDeleteTemplate();

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteTemplate.mutateAsync(templateId);
      router.push('/session-templates');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEdit = () => {
    router.push(`/session-templates/${templateId}/edit`);
  };

  const handleUseTemplate = () => {
    router.push(`/sessions/new?templateId=${templateId}`);
  };

  const handleShare = () => {
    // Navigate to sharing settings or open dialog
    // This would typically open a sharing dialog
    alert('Share functionality - to be implemented with SharingDialog component');
  };

  if (isLoading) {
    return (
      <AppLayout title="Template Details">
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <Skeleton className="h-8 w-64 mb-6" />
          <div className="space-y-6">
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-96 w-full" />
          </div>
        </div>
      </AppLayout>
    );
  }

  if (!template) {
    return (
      <AppLayout title="Template Not Found">
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500 mb-4">Template not found</p>
              <Button variant="outline" onClick={() => router.push('/session-templates')}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Templates
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title={template.name}>
      <div className="container mx-auto py-8 px-4 max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/session-templates')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold">{template.name}</h1>
                {template.category && (
                  <Badge variant="secondary" className="capitalize">
                    {template.category}
                  </Badge>
                )}
              </div>
              {template.description && (
                <p className="text-gray-500 mt-1">{template.description}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button onClick={handleUseTemplate}>
              <Copy className="h-4 w-4 mr-2" />
              Use Template
            </Button>
            <Button variant="outline" onClick={handleEdit}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
            <Button variant="outline" onClick={handleShare}>
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={isDeleting}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>

        {/* Template Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Usage Stats */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">Usage Count</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{template.usage_count}</p>
              {template.last_used_at && (
                <p className="text-sm text-gray-500 mt-1">
                  Last used {format(new Date(template.last_used_at), 'MMM d, yyyy')}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Version */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">Version</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{template.version}</p>
              <p className="text-sm text-gray-500 mt-1">
                Updated {format(new Date(template.updated_at), 'MMM d, yyyy')}
              </p>
            </CardContent>
          </Card>

          {/* Visibility */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">Visibility</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-2">
                {template.is_public && (
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-blue-600" />
                    <Badge variant="outline">Public</Badge>
                  </div>
                )}
                {template.is_organization_shared && (
                  <div className="flex items-center gap-2">
                    <Building className="h-4 w-4 text-purple-600" />
                    <Badge variant="outline">Organization</Badge>
                  </div>
                )}
                {!template.is_public && !template.is_organization_shared && (
                  <Badge variant="outline">Private</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Tag className="h-5 w-5" />
                Tags
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {template.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Configuration Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* System Prompt */}
          {template.system_prompt && (
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>System Prompt</CardTitle>
                <CardDescription>
                  The default system prompt used when creating sessions from this template
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap font-mono overflow-auto max-h-96">
                  {template.system_prompt}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Working Directory */}
          {template.working_directory && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Folder className="h-5 w-5" />
                  Working Directory
                </CardTitle>
              </CardHeader>
              <CardContent>
                <code className="bg-gray-100 px-3 py-2 rounded text-sm font-mono block">
                  {template.working_directory}
                </code>
              </CardContent>
            </Card>
          )}

          {/* Allowed Tools */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Allowed Tools
              </CardTitle>
            </CardHeader>
            <CardContent>
              {template.allowed_tools.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {template.allowed_tools.map((tool) => (
                    <Badge key={tool} variant="outline" className="font-mono">
                      {tool}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">All tools allowed</p>
              )}
            </CardContent>
          </Card>

          {/* SDK Options */}
          {template.sdk_options && Object.keys(template.sdk_options).length > 0 && (
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>SDK Options</CardTitle>
                <CardDescription>
                  Claude Agent SDK configuration options
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96 font-mono">
                  {JSON.stringify(template.sdk_options, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* MCP Servers */}
          {template.mcp_server_ids && template.mcp_server_ids.length > 0 && (
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>MCP Servers</CardTitle>
                <CardDescription>
                  Model Context Protocol servers configured for this template
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {template.mcp_server_ids.map((serverId) => (
                    <Badge key={serverId} variant="secondary" className="font-mono">
                      {serverId}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Metadata */}
          {template.template_metadata && Object.keys(template.template_metadata).length > 0 && (
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Template Metadata</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96 font-mono">
                  {JSON.stringify(template.template_metadata, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Timestamps */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 font-medium mb-1">Created</p>
                <p>{format(new Date(template.created_at), 'PPpp')}</p>
              </div>
              <div>
                <p className="text-gray-500 font-medium mb-1">Last Updated</p>
                <p>{format(new Date(template.updated_at), 'PPpp')}</p>
              </div>
              {template.last_used_at && (
                <div>
                  <p className="text-gray-500 font-medium mb-1">Last Used</p>
                  <p>{format(new Date(template.last_used_at), 'PPpp')}</p>
                </div>
              )}
              <div>
                <p className="text-gray-500 font-medium mb-1">Template ID</p>
                <code className="text-xs bg-gray-100 px-2 py-1 rounded">{template.id}</code>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
