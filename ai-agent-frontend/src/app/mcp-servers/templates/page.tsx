'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CreateServerDialog } from '@/components/mcp/create-server-dialog';
import { useMCPTemplates } from '@/hooks/use-mcp-servers';
import { MCPServerType } from '@/types/api';
import { Search, ArrowLeft, Server, Zap, Globe } from 'lucide-react';
import Link from 'next/link';
import { Skeleton } from '@/components/ui/skeleton';
import { getTypeBgColor, getTypeColor } from '@/components/mcp/type-selector';

function TemplatesContent() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const { data, isLoading } = useMCPTemplates();
  const templates = data?.templates || [];

  // Filter templates
  const filteredTemplates = templates.filter((template: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      template.name?.toLowerCase().includes(query) ||
      template.description?.toLowerCase().includes(query)
    );
  });

  const handleUseTemplate = (template: any) => {
    setSelectedTemplate(template);
    setCreateDialogOpen(true);
  };

  const getTypeIcon = (type: MCPServerType) => {
    if (type === 'stdio') return Server;
    if (type === 'sse') return Zap;
    return Globe;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/mcp-servers">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Servers
              </Link>
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Server Templates</h1>
              <p className="text-gray-600 mt-1">
                Pre-configured templates for popular MCP servers
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Templates Grid */}
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
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border">
            <div className="text-gray-400 mb-4">
              <Search className="mx-auto h-12 w-12" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No templates found</h3>
            <p className="text-gray-600">Try adjusting your search query</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((template: any, index: number) => {
              const TypeIcon = getTypeIcon(template.server_type);
              return (
                <Card
                  key={index}
                  className="hover:shadow-lg transition-shadow cursor-pointer group"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between mb-2">
                      <div
                        className={`w-12 h-12 rounded-lg flex items-center justify-center ${getTypeBgColor(
                          template.server_type
                        )}`}
                      >
                        <TypeIcon className={`h-6 w-6 ${getTypeColor(template.server_type)}`} />
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {template.server_type.toUpperCase()}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {template.description}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {/* Required Config */}
                    {template.required_config && template.required_config.length > 0 && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs font-medium text-gray-500 mb-2">
                          Required Configuration
                        </div>
                        <div className="space-y-1">
                          {template.required_config.map((config: string, i: number) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <div className="w-1 h-1 rounded-full bg-gray-400" />
                              <span className="text-gray-700">{config}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Config Preview */}
                    {template.config && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="text-xs font-medium text-gray-500 mb-2">
                          Configuration Preview
                        </div>
                        {template.server_type === 'stdio' && template.config.command && (
                          <div className="text-sm">
                            <code className="text-xs bg-white px-1.5 py-0.5 rounded">
                              {template.config.command}
                              {template.config.args &&
                                template.config.args.length > 0 &&
                                ` (${template.config.args.length} args)`}
                            </code>
                          </div>
                        )}
                        {(template.server_type === 'sse' || template.server_type === 'http') &&
                          template.config.url && (
                            <div className="text-sm">
                              <code className="text-xs bg-white px-1.5 py-0.5 rounded break-all">
                                {template.config.url}
                              </code>
                            </div>
                          )}
                      </div>
                    )}

                    {/* Action */}
                    <Button
                      className="w-full"
                      onClick={() => handleUseTemplate(template)}
                      variant="outline"
                    >
                      Use This Template
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Results count */}
        {!isLoading && filteredTemplates.length > 0 && (
          <div className="text-center mt-6 text-sm text-gray-600">
            Showing {filteredTemplates.length} of {templates.length} templates
          </div>
        )}
      </div>

      {/* Create Dialog */}
      <CreateServerDialog
        open={createDialogOpen}
        onOpenChange={(open) => {
          setCreateDialogOpen(open);
          if (!open) setSelectedTemplate(null);
        }}
        template={selectedTemplate}
      />
    </div>
  );
}

export default function TemplatesPage() {
  return (
    <ProtectedRoute>
      <TemplatesContent />
    </ProtectedRoute>
  );
}
