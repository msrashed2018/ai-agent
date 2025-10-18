import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { useDownloadReport } from '@/hooks/use-reports';
import type { ReportResponse } from '@/types/api';

interface DownloadButtonsProps {
  report: ReportResponse;
  formats?: string[];
}

export function DownloadButtons({ report, formats = ['html', 'pdf', 'json', 'markdown'] }: DownloadButtonsProps) {
  const downloadReport = useDownloadReport();

  const handleDownload = (format: string) => {
    const extension = format === 'markdown' ? 'md' : format;
    const fileName = `${report.title.replace(/\s+/g, '_')}_${report.id.slice(0, 8)}.${extension}`;

    downloadReport.mutate({
      reportId: report.id,
      format,
      fileName,
    });
  };

  const getFormatLabel = (format: string) => {
    const labels: Record<string, string> = {
      html: 'HTML',
      pdf: 'PDF',
      json: 'JSON',
      markdown: 'Markdown',
    };
    return labels[format] || format.toUpperCase();
  };

  return (
    <div className="flex gap-2 flex-wrap">
      {formats.map((format) => (
        <Button
          key={format}
          variant="outline"
          size="sm"
          onClick={() => handleDownload(format)}
          disabled={downloadReport.isPending}
        >
          <Download className="h-4 w-4 mr-2" />
          {getFormatLabel(format)}
        </Button>
      ))}
    </div>
  );
}
