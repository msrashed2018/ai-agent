import { Badge } from '@/components/ui/badge';
import { PlayCircle, FileEdit, Calendar, Sparkles } from 'lucide-react';

interface TypeBadgeProps {
  type: string;
}

export function TypeBadge({ type }: TypeBadgeProps) {
  const getTypeConfig = (reportType: string) => {
    switch (reportType) {
      case 'task_execution':
        return {
          icon: PlayCircle,
          label: 'Task Execution',
          className: 'bg-blue-100 text-blue-700 border-blue-200',
        };
      case 'manual':
        return {
          icon: FileEdit,
          label: 'Manual',
          className: 'bg-gray-100 text-gray-700 border-gray-200',
        };
      case 'scheduled':
        return {
          icon: Calendar,
          label: 'Scheduled',
          className: 'bg-purple-100 text-purple-700 border-purple-200',
        };
      case 'auto_generated':
        return {
          icon: Sparkles,
          label: 'Auto Generated',
          className: 'bg-green-100 text-green-700 border-green-200',
        };
      default:
        return {
          icon: FileEdit,
          label: reportType,
          className: 'bg-gray-100 text-gray-700 border-gray-200',
        };
    }
  };

  const config = getTypeConfig(type);
  const Icon = config.icon;

  return (
    <Badge className={config.className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}
