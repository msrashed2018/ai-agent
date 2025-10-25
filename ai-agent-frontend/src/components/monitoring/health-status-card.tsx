'use client';

import { AlertCircle, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';
import type { HealthCheckResponse } from '@/types/api';

interface HealthStatusCardProps {
  title: string;
  health: HealthCheckResponse | undefined;
  isLoading: boolean;
  error?: Error | null;
}

export function HealthStatusCard({
  title,
  health,
  isLoading,
  error,
}: HealthStatusCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="animate-pulse h-8 bg-gray-200 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold text-red-900">{title}</h3>
            <p className="text-sm text-red-700 mt-1">Failed to load health status</p>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <p className="text-sm text-gray-500">No health data available</p>
      </div>
    );
  }

  const statusConfig = {
    healthy: {
      icon: CheckCircle2,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      badgeColor: 'bg-green-100 text-green-800',
    },
    degraded: {
      icon: AlertTriangle,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-900',
      badgeColor: 'bg-yellow-100 text-yellow-800',
    },
    unhealthy: {
      icon: AlertCircle,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-900',
      badgeColor: 'bg-red-100 text-red-800',
    },
    unknown: {
      icon: HelpCircle,
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
      textColor: 'text-gray-900',
      badgeColor: 'bg-gray-100 text-gray-800',
    },
  };

  const status = (health.status || 'unknown') as keyof typeof statusConfig;
  const config = statusConfig[status] || statusConfig.unknown;
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-6`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3 flex-1">
          <Icon className={`h-6 w-6 ${config.textColor}`} />
          <div>
            <h3 className={`text-lg font-semibold ${config.textColor}`}>{title}</h3>
            <p className={`text-sm ${config.textColor} opacity-75 mt-1`}>
              {`Status: ${status}`}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.badgeColor}`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>

      {health.components && Object.keys(health.components).length > 0 && (
        <div className="mt-4 pt-4 border-t border-current border-opacity-20">
          <h4 className="text-sm font-medium mb-2 opacity-75">Components:</h4>
          <dl className="space-y-2 text-sm">
            {Object.entries(health.components).map(([name, component]) => (
              <div key={name}>
                <dt className={`font-medium ${config.textColor} opacity-75`}>
                  {name.replace(/_/g, ' ')}
                </dt>
                <dd className={`${config.textColor} text-xs opacity-75 mt-0.5`}>
                  {component.message || `Status: ${component.status}`}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
