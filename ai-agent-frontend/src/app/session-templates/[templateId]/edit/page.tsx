'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { TemplateForm } from '@/components/session-templates/template-form';
import { useSessionTemplate, useUpdateTemplate } from '@/hooks/use-session-templates';
import { SessionTemplateUpdateRequest } from '@/types/api';
import { AppLayout } from '@/components/layout/app-layout';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function EditTemplatePage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.templateId as string;

  const { data: template, isLoading } = useSessionTemplate(templateId);
  const updateTemplate = useUpdateTemplate();

  const handleSubmit = async (data: SessionTemplateUpdateRequest) => {
    await updateTemplate.mutateAsync({ templateId, data });
    router.push(`/session-templates/${templateId}`);
  };

  if (isLoading) {
    return (
      <AppLayout title="Edit Template">
        <div className="container mx-auto py-8 px-4 max-w-4xl">
          <Skeleton className="h-8 w-64 mb-6" />
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48 mb-2" />
              <Skeleton className="h-4 w-96" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  if (!template) {
    return (
      <AppLayout title="Template Not Found">
        <div className="container mx-auto py-8 px-4 max-w-4xl">
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500 mb-4">Template not found</p>
              <Link href="/session-templates">
                <Button variant="outline">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Templates
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Edit Template">
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <div className="mb-6">
          <Link href={`/session-templates/${templateId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Template
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Edit Template: {template.name}</CardTitle>
            <CardDescription>
              Update template configuration and settings. Changes will be reflected in future sessions created from this template.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TemplateForm
              template={template}
              onSubmit={handleSubmit}
              isSubmitting={updateTemplate.isPending}
              submitLabel="Update Template"
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
