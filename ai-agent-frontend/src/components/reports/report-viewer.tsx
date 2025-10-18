import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import type { ReportResponse } from '@/types/api';

interface ReportViewerProps {
  report: ReportResponse;
}

export function ReportViewer({ report }: ReportViewerProps) {
  const renderContent = () => {
    if (!report.content) {
      return (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>No content available for this report.</AlertDescription>
        </Alert>
      );
    }

    const format = report.file_format?.toLowerCase();

    switch (format) {
      case 'html':
        return (
          <div className="border rounded-lg overflow-hidden">
            <iframe
              srcDoc={typeof report.content === 'string' ? report.content : JSON.stringify(report.content)}
              className="w-full h-[600px] border-0"
              sandbox="allow-same-origin"
              title="Report Content"
            />
          </div>
        );

      case 'json':
        return (
          <div className="border rounded-lg overflow-hidden">
            <pre className="p-4 bg-gray-50 overflow-auto max-h-[600px]">
              <code className="text-sm">
                {JSON.stringify(report.content, null, 2)}
              </code>
            </pre>
          </div>
        );

      case 'markdown':
        return (
          <div className="border rounded-lg p-4 bg-white">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                {typeof report.content === 'string' ? report.content : JSON.stringify(report.content, null, 2)}
              </pre>
            </div>
          </div>
        );

      case 'pdf':
        return (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              PDF preview is not available. Please use the download button to view the PDF.
            </AlertDescription>
          </Alert>
        );

      default:
        return (
          <div className="border rounded-lg overflow-hidden">
            <pre className="p-4 bg-gray-50 overflow-auto max-h-[600px]">
              <code className="text-sm">
                {typeof report.content === 'string' ? report.content : JSON.stringify(report.content, null, 2)}
              </code>
            </pre>
          </div>
        );
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report Content</CardTitle>
      </CardHeader>
      <CardContent>{renderContent()}</CardContent>
    </Card>
  );
}
