import { Badge } from '@/components/ui/badge';
import { HealthStatus } from '@/types/api';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';

interface HealthBadgeProps {
  status: HealthStatus | null | undefined;
  showIcon?: boolean;
}

export function HealthBadge({ status, showIcon = true }: HealthBadgeProps) {
  if (!status || status === 'unknown') {
    return (
      <Badge variant="secondary" className="gap-1">
        {showIcon && <HelpCircle className="h-3 w-3" />}
        Unknown
      </Badge>
    );
  }

  if (status === 'healthy') {
    return (
      <Badge variant="default" className="gap-1 bg-green-600 hover:bg-green-700">
        {showIcon && <CheckCircle2 className="h-3 w-3" />}
        Healthy
      </Badge>
    );
  }

  return (
    <Badge variant="destructive" className="gap-1">
      {showIcon && <XCircle className="h-3 w-3" />}
      Unhealthy
    </Badge>
  );
}
