'use client';

import { useState, useMemo } from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ServerCard } from '@/components/mcp/server-card';
import { CreateServerDialog } from '@/components/mcp/create-server-dialog';
import { ImportConfigDialog } from '@/components/mcp/import-config-dialog';
import { ExportConfigDialog } from '@/components/mcp/export-config-dialog';
import {
  useMCPServers,
  useUpdateMCPServer,
  useDeleteMCPServer,
  useHealthCheck,
} from '@/hooks/use-mcp-servers';
import { MCPServerType, HealthStatus, MCPServerResponse } from '@/types/api';
import { Plus, Upload, Download, Search, Palette } from 'lucide-react';
import Link from 'next/link';
import { Skeleton } from '@/components/ui/skeleton';

function MCPServersContent() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<MCPServerType | 'all'>('all');
  const [healthFilter, setHealthFilter] = useState<HealthStatus | 'all'>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

  const { data, isLoading } = useMCPServers();
  const updateMutation = useUpdateMCPServer();
  const deleteMutation = useDeleteMCPServer();
  const healthCheckMutation = useHealthCheck();

  const servers = data?.items || [];

  // Filter servers
  const filteredServers = useMemo(() => {
    return servers.filter((server) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (
          !server.name.toLowerCase().includes(query) &&
          !server.description?.toLowerCase().includes(query)
        ) {
          return false;
        }
      }

      // Type filter
      if (typeFilter !== 'all' && server.server_type !== typeFilter) {
        return false;
      }

      // Health filter
      if (healthFilter !== 'all') {
        if (healthFilter === 'unknown' && server.health_status !== null && server.health_status !== 'unknown') {
          return false;
        } else if (healthFilter !== 'unknown' && server.health_status !== healthFilter) {
          return false;
        }
      }

      return true;
    });
  }, [servers, searchQuery, typeFilter, healthFilter]);

  const handleEdit = (server: MCPServerResponse) => {
    // TODO: Open edit dialog
    console.log('Edit server:', server);
  };

  const handleDelete = async (serverId: string) => {
    if (confirm('Are you sure you want to delete this server?')) {
      await deleteMutation.mutateAsync(serverId);
    }
  };

  const handleHealthCheck = async (serverId: string) => {
    await healthCheckMutation.mutateAsync(serverId);
  };

  const handleToggleEnabled = async (serverId: string, enabled: boolean) => {
    await updateMutation.mutateAsync({
      serverId,
      data: { is_enabled: enabled },
    });
  };

  // Stats
  const stats = useMemo(() => {
    return {
      total: servers.length,
      enabled: servers.filter((s) => s.is_enabled).length,
      healthy: servers.filter((s) => s.health_status === 'healthy').length,
      user: servers.filter((s) => !s.is_global).length,
      global: servers.filter((s) => s.is_global).length,
    };
  }, [servers]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">MCP Servers</h1>
              <p className="text-gray-600 mt-1">Manage your Model Context Protocol servers</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setImportDialogOpen(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
              <Button variant="outline" onClick={() => setExportDialogOpen(true)}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Server
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-5 gap-4 mt-6">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-gray-600">Total Servers</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-700">{stats.enabled}</div>
              <div className="text-xs text-gray-600">Enabled</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-700">{stats.healthy}</div>
              <div className="text-xs text-gray-600">Healthy</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-purple-700">{stats.user}</div>
              <div className="text-xs text-gray-600">User Servers</div>
            </div>
            <div className="bg-amber-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-amber-700">{stats.global}</div>
              <div className="text-xs text-gray-600">Global Servers</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search servers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as any)}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="stdio">STDIO</SelectItem>
                <SelectItem value="sse">SSE</SelectItem>
                <SelectItem value="http">HTTP</SelectItem>
              </SelectContent>
            </Select>
            <Select value={healthFilter} onValueChange={(v) => setHealthFilter(v as any)}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by health" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Health Status</SelectItem>
                <SelectItem value="healthy">Healthy</SelectItem>
                <SelectItem value="unhealthy">Unhealthy</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Quick Link to Templates */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">Browse Server Templates</h3>
                <p className="text-sm text-gray-600">
                  Get started quickly with pre-configured MCP servers
                </p>
              </div>
            </div>
            <Button variant="outline" asChild>
              <Link href="/mcp-servers/templates">View Templates</Link>
            </Button>
          </div>
        </div>

        {/* Server Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="border rounded-lg p-6">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full mb-4" />
                <Skeleton className="h-20 w-full" />
              </div>
            ))}
          </div>
        ) : filteredServers.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border">
            <div className="text-gray-400 mb-4">
              <svg
                className="mx-auto h-12 w-12"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No servers found</h3>
            <p className="text-gray-600 mb-4">
              {servers.length === 0
                ? 'Get started by creating your first MCP server'
                : 'Try adjusting your filters'}
            </p>
            {servers.length === 0 && (
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Server
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredServers.map((server) => (
              <ServerCard
                key={server.id}
                server={server}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onHealthCheck={handleHealthCheck}
                onToggleEnabled={handleToggleEnabled}
              />
            ))}
          </div>
        )}

        {/* Results count */}
        {!isLoading && filteredServers.length > 0 && (
          <div className="text-center mt-6 text-sm text-gray-600">
            Showing {filteredServers.length} of {servers.length} servers
          </div>
        )}
      </div>

      {/* Dialogs */}
      <CreateServerDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
      <ImportConfigDialog open={importDialogOpen} onOpenChange={setImportDialogOpen} />
      <ExportConfigDialog open={exportDialogOpen} onOpenChange={setExportDialogOpen} />
    </div>
  );
}

export default function MCPServersPage() {
  return (
    <ProtectedRoute>
      <MCPServersContent />
    </ProtectedRoute>
  );
}
