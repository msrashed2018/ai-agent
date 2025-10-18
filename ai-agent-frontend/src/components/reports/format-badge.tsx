import { Badge } from '@/components/ui/badge';
import { FileText, FileJson, File, FileCode } from 'lucide-react';
import type { ReportFormat } from '@/types/api';

interface FormatBadgeProps {
  format: ReportFormat | string;
}

export function FormatBadge({ format }: FormatBadgeProps) {
  const getFormatConfig = (fmt: string) => {
    switch (fmt.toLowerCase()) {
      case 'html':
        return {
          icon: FileText,
          label: 'HTML',
          className: 'bg-blue-100 text-blue-700 border-blue-200',
        };
      case 'pdf':
        return {
          icon: File,
          label: 'PDF',
          className: 'bg-red-100 text-red-700 border-red-200',
        };
      case 'json':
        return {
          icon: FileJson,
          label: 'JSON',
          className: 'bg-green-100 text-green-700 border-green-200',
        };
      case 'markdown':
        return {
          icon: FileCode,
          label: 'Markdown',
          className: 'bg-purple-100 text-purple-700 border-purple-200',
        };
      default:
        return {
          icon: File,
          label: fmt.toUpperCase(),
          className: 'bg-gray-100 text-gray-700 border-gray-200',
        };
    }
  };

  const config = getFormatConfig(format);
  const Icon = config.icon;

  return (
    <Badge className={config.className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}
