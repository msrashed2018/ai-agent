import Link from 'next/link';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { FormatBadge } from './format-badge';
import { TypeBadge } from './type-badge';
import { useDownloadReport } from '@/hooks/use-reports';
import { Eye, Download } from 'lucide-react';
import { formatDate, formatBytes } from '@/lib/utils';
import type { ReportResponse } from '@/types/api';

interface ReportTableProps {
  reports: ReportResponse[] | undefined;
  loading?: boolean;
}

export function ReportTable({ reports, loading }: ReportTableProps) {
  const downloadReport = useDownloadReport();

  const handleQuickDownload = (report: ReportResponse, format: string) => {
    const extension = format === 'markdown' ? 'md' : format;
    const fileName = `${report.title.replace(/\s+/g, '_')}_${report.id.slice(0, 8)}.${extension}`;

    downloadReport.mutate({
      reportId: report.id,
      format,
      fileName,
    });
  };

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!reports || reports.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No reports found</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Format</TableHead>
            <TableHead>File Size</TableHead>
            <TableHead>Session</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.map((report) => (
            <TableRow key={report.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{report.title}</div>
                  {report.description && (
                    <div className="text-sm text-gray-500 truncate max-w-md">
                      {report.description}
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <TypeBadge type={report.report_type} />
              </TableCell>
              <TableCell>
                <FormatBadge format={report.file_format || 'unknown'} />
              </TableCell>
              <TableCell className="text-sm text-gray-600">
                {report.file_size_bytes ? formatBytes(report.file_size_bytes) : 'N/A'}
              </TableCell>
              <TableCell>
                <Link
                  href={`/sessions/${report.session_id}`}
                  className="text-blue-600 hover:underline text-sm"
                >
                  {report.session_id.slice(0, 8)}...
                </Link>
              </TableCell>
              <TableCell className="text-sm text-gray-600">
                {formatDate(report.created_at)}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Link href={`/reports/${report.id}`}>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickDownload(report, report.file_format || 'html')}
                    disabled={downloadReport.isPending}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Download
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
