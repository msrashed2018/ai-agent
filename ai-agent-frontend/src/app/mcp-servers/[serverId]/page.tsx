'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { HealthBadge } from '@/components/mcp/health-badge';
import {
  useMCPServer,
  useUpdateMCPServer,
  useDeleteMCPServer,
  useHealthCheck,
} from '@/hooks/use-mcp-servers';
import { ArrowLeft, Edit, Trash2, Activity, Globe, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { Skeleton } from '@/components/ui/skeleton';
import { getTypeBgColor, getTypeColor } from '@/components/mcp/type-selector';

function ServerDetailContent() {
  const params = useParams();
  const router = useRouter();
  const serverId = params.serverId as string;

  const { data: server, isLoading } = useMCPServer(serverId);
  const updateMutation = useUpdateMCPServer();
  const deleteMutation = useDeleteMCPServer();
  const healthCheckMutation = useHealthCheck();

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this server?')) {
      await deleteMutation.mutateAsync(serverId);
      router.push('/mcp-servers');
    }
  };

  const handleHealthCheck = async () => {
    await healthCheckMutation.mutateAsync(serverId);
  };

  const handleToggleEnabled = async (enabled: boolean) => {
    await updateMutation.mutateAsync({
      serverId,
      data: { is_enabled: enabled },
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!server) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Server not found</h2>
          <Button asChild>
            <Link href="/mcp-servers">Back to Servers</Link>
          </Button>
        </div>
      </div>
    );
  }

  const isReadOnly = server.is_global;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/mcp-servers">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Servers
              </Link>
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900">{server.name}</h1>
              {server.is_global && (
                <Badge variant="secondary" className="text-sm">
                  <Globe className="h-3 w-3 mr-1" />
                  Global
                </Badge>
              )}
              <HealthBadge status={server.health_status} />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleHealthCheck}
                disabled={healthCheckMutation.isPending}
              >
                {healthCheckMutation.isPending ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Activity className="h-4 w-4 mr-2" />
                )}
                Health Check
              </Button>
              <Button variant="outline" disabled={isReadOnly}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="outline"
                onClick={handleDelete}
                disabled={isReadOnly || deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-gray-600">Name</Label>
                  <div className="text-lg font-medium">{server.name}</div>
                </div>
                {server.description && (
                  <div>
                    <Label className="text-gray-600">Description</Label>
                    <div className="text-sm">{server.description}</div>
                  </div>
                )}
                <div>
                  <Label className="text-gray-600">Server Type</Label>
                  <div>
                    <Badge
                      variant="secondary"
                      className={`${getTypeBgColor(server.server_type)} mt-1`}
                    >
                      <span className={`font-medium ${getTypeColor(server.server_type)}`}>
                        {server.server_type.toUpperCase()}
                      </span>
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>Configuration</CardTitle>
                <CardDescription>Server connection and runtime configuration</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(server.config, null, 2)}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Status & Settings */}
          <div className="space-y-6">
            {/* Status */}
            <Card>
              <CardHeader>
                <CardTitle>Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Enabled</Label>
                    <p className="text-xs text-gray-500">
                      Available for use in sessions
                    </p>
                  </div>
                  <Switch
                    checked={server.is_enabled}
                    onCheckedChange={handleToggleEnabled}
                    disabled={isReadOnly || updateMutation.isPending}
                  />
                </div>
                <div>
                  <Label className="text-gray-600">Health Status</Label>
                  <div className="mt-2">
                    <HealthBadge status={server.health_status} />
                  </div>
                </div>
                {server.last_health_check_at && (
                  <div>
                    <Label className="text-gray-600">Last Health Check</Label>
                    <div className="text-sm mt-1">
                      {new Date(server.last_health_check_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle>Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label className="text-gray-600">Server ID</Label>
                  <div className="text-xs font-mono mt-1 bg-gray-50 p-2 rounded break-all">
                    {server.id}
                  </div>
                </div>
                <div>
                  <Label className="text-gray-600">Created At</Label>
                  <div className="text-sm mt-1">
                    {new Date(server.created_at).toLocaleString()}
                  </div>
                </div>
                <div>
                  <Label className="text-gray-600">Updated At</Label>
                  <div className="text-sm mt-1">
                    {new Date(server.updated_at).toLocaleString()}
                  </div>
                </div>
                <div>
                  <Label className="text-gray-600">Scope</Label>
                  <div className="mt-1">
                    <Badge variant={server.is_global ? 'secondary' : 'default'}>
                      {server.is_global ? 'Global' : 'User'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ServerDetailPage() {
  return (
    <ProtectedRoute>
      <ServerDetailContent />
    </ProtectedRoute>
  );
}
