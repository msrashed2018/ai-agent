'use client';

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useReport } from '@/hooks/use-reports';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ReportViewer } from '@/components/reports/report-viewer';
import { DownloadButtons } from '@/components/reports/download-buttons';
import { FormatBadge } from '@/components/reports/format-badge';
import { TypeBadge } from '@/components/reports/type-badge';
import { ArrowLeft, ExternalLink, Calendar, FileText } from 'lucide-react';
import { formatDate, formatBytes } from '@/lib/utils';

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.reportId as string;

  const { data: report, isLoading, error } = useReport(reportId);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-6">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-600">Failed to load report</p>
            <Button onClick={() => router.back()} className="mt-4">
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <FileText className="h-8 w-8" />
              {report.title}
            </h1>
            {report.description && (
              <p className="text-gray-600 mt-2">{report.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Report Info Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Report Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-500 mb-1">Type</div>
              <TypeBadge type={report.report_type} />
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">Format</div>
              <FormatBadge format={report.file_format || 'unknown'} />
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">File Size</div>
              <div className="font-medium">
                {report.file_size_bytes ? formatBytes(report.file_size_bytes) : 'N/A'}
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">Created</div>
              <div className="font-medium flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(report.created_at)}
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">Session</div>
              <Link
                href={`/sessions/${report.session_id}`}
                className="text-blue-600 hover:underline flex items-center gap-1"
              >
                {report.session_id.slice(0, 8)}...
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>

            {report.task_execution_id && (
              <div>
                <div className="text-sm text-gray-500 mb-1">Task Execution</div>
                <Link
                  href={`/tasks/executions/${report.task_execution_id}`}
                  className="text-blue-600 hover:underline flex items-center gap-1"
                >
                  {report.task_execution_id.slice(0, 8)}...
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </div>
            )}

            {report.tags && report.tags.length > 0 && (
              <div className="col-span-full">
                <div className="text-sm text-gray-500 mb-2">Tags</div>
                <div className="flex gap-2 flex-wrap">
                  {report.tags.map((tag, idx) => (
                    <Badge key={idx} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-6 border-t">
            <div className="text-sm text-gray-500 mb-3">Download Report</div>
            <DownloadButtons report={report} />
          </div>
        </CardContent>
      </Card>

      {/* Report Content Viewer */}
      <ReportViewer report={report} />
    </div>
  );
}
