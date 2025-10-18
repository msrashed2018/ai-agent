'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, LayoutGrid, Table as TableIcon } from 'lucide-react';
import { useSessionTemplates } from '@/hooks/use-session-templates';
import { TemplateCard } from '@/components/session-templates/template-card';
import { TemplateTable } from '@/components/session-templates/template-table';
import { SearchBar } from '@/components/session-templates/search-bar';
import { SharingDialog } from '@/components/session-templates/sharing-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { SessionTemplateResponse, SessionTemplateSearchRequest } from '@/types/api';
import { AppLayout } from '@/components/layout/app-layout';

export default function SessionTemplatesPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [searchParams, setSearchParams] = useState<SessionTemplateSearchRequest | null>(null);
  const [sharingTemplate, setSharingTemplate] = useState<SessionTemplateResponse | null>(null);

  const { data, isLoading, error } = useSessionTemplates({ page, page_size: pageSize });

  const handleSearch = (params: SessionTemplateSearchRequest) => {
    setSearchParams(params);
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchParams(null);
    setPage(1);
  };

  const handleEdit = (template: SessionTemplateResponse) => {
    router.push(`/session-templates/${template.id}/edit`);
  };

  const handleShare = (template: SessionTemplateResponse) => {
    setSharingTemplate(template);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Session Templates</h1>
            <p className="text-muted-foreground mt-1">
              Create and manage reusable session templates
            </p>
          </div>
          <Button onClick={() => router.push('/session-templates/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Template
          </Button>
        </div>

        {/* Search Bar */}
        <SearchBar onSearch={handleSearch} onClear={handleClearSearch} />

        {/* View Mode Tabs */}
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'grid' | 'table')}>
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="grid">
                <LayoutGrid className="mr-2 h-4 w-4" />
                Grid
              </TabsTrigger>
              <TabsTrigger value="table">
                <TableIcon className="mr-2 h-4 w-4" />
                Table
              </TabsTrigger>
            </TabsList>

            {data && (
              <p className="text-sm text-muted-foreground">
                Showing {data.items.length} of {data.total} templates
              </p>
            )}
          </div>

          {/* Grid View */}
          <TabsContent value="grid" className="mt-6">
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <Skeleton key={i} className="h-80" />
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">Failed to load templates</p>
              </div>
            ) : data && data.items.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    onEdit={handleEdit}
                    onShare={handleShare}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">No templates found</p>
                <Button onClick={() => router.push('/session-templates/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Template
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Table View */}
          <TabsContent value="table" className="mt-6">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">Failed to load templates</p>
              </div>
            ) : data && data.items.length > 0 ? (
              <TemplateTable
                templates={data.items}
                onEdit={(templateId) => router.push(`/session-templates/${templateId}/edit`)}
                onShare={handleShare}
              />
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">No templates found</p>
                <Button onClick={() => router.push('/session-templates/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Template
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {data.total_pages}
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page === data.total_pages}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Sharing Dialog */}
      {sharingTemplate && (
        <SharingDialog
          template={sharingTemplate}
          open={!!sharingTemplate}
          onClose={() => setSharingTemplate(null)}
        />
      )}
    </AppLayout>
  );
}
