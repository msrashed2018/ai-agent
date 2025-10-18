'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TemplateForm } from '@/components/session-templates/template-form';
import { useCreateTemplate } from '@/hooks/use-session-templates';
import { SessionTemplateCreateRequest, SessionTemplateUpdateRequest } from '@/types/api';
import { AppLayout } from '@/components/layout/app-layout';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewTemplatePage() {
  const router = useRouter();
  const createTemplate = useCreateTemplate();

  const handleSubmit = async (data: SessionTemplateCreateRequest | SessionTemplateUpdateRequest) => {
    await createTemplate.mutateAsync(data as SessionTemplateCreateRequest);
    router.push('/session-templates');
  };

  return (
    <AppLayout title="Create Session Template">
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <div className="mb-6">
          <Link href="/session-templates">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Templates
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create Session Template</CardTitle>
            <CardDescription>
              Create a reusable template for session configuration. Templates can be used to quickly create new sessions with predefined settings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TemplateForm
              onSubmit={handleSubmit}
              isSubmitting={createTemplate.isPending}
              submitLabel="Create Template"
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
