'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { TemplateCard } from '@/components/session-templates/template-card';
import { usePopularTemplates } from '@/hooks/use-session-templates';
import { AppLayout } from '@/components/layout/app-layout';
import { ArrowLeft, TrendingUp } from 'lucide-react';
import { SessionTemplateResponse } from '@/types/api';

export default function PopularTemplatesPage() {
  const router = useRouter();
  const { data: templates, isLoading } = usePopularTemplates();

  const handleEdit = (template: SessionTemplateResponse) => {
    router.push(`/session-templates/${template.id}/edit`);
  };

  const handleShare = (template: SessionTemplateResponse) => {
    // This would typically open a sharing dialog
    alert('Share functionality - to be implemented with SharingDialog component');
  };

  if (isLoading) {
    return (
      <AppLayout title="Popular Templates">
        <div className="container mx-auto py-8 px-4 max-w-7xl">
          <Skeleton className="h-8 w-64 mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-96 w-full" />
            ))}
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Popular Templates">
      <div className="container mx-auto py-8 px-4 max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/session-templates')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <TrendingUp className="h-8 w-8" />
                Top Popular Templates
              </h1>
              <p className="text-gray-500 mt-1">
                Most frequently used session templates by the community
              </p>
            </div>
          </div>
        </div>

        {/* Templates Grid */}
        {templates && templates.items && templates.items.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.items.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onEdit={handleEdit}
                onShare={handleShare}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Popular Templates Yet
              </h3>
              <p className="text-gray-500 mb-6">
                Popular templates will appear here as they gain usage across the platform.
              </p>
              <Button onClick={() => router.push('/session-templates/new')}>
                Create Your First Template
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Stats Summary */}
        {templates && templates.items && templates.items.length > 0 && (
          <Card>
            <CardContent className="py-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                <div>
                  <p className="text-3xl font-bold text-blue-600">
                    {templates.items.length}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Popular Templates</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-green-600">
                    {templates.items.reduce((sum, t) => sum + t.usage_count, 0)}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Total Usage Count</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-purple-600">
                    {templates.items.filter(t => t.is_public).length}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Public Templates</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
