'use client';

import { useSessionMetrics } from '@/hooks/use-sessions';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface SessionMetricsPanelProps {
  sessionId: string;
}

export function SessionMetricsPanel({ sessionId }: SessionMetricsPanelProps) {
  const { data: metrics, isLoading } = useSessionMetrics(sessionId);

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  if (!metrics) {
    return null;
  }

  const { current_metrics, performance_trends } = metrics;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Session Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Messages" value={current_metrics.total_messages} />
        <MetricCard label="Tool Calls" value={current_metrics.total_tool_calls} />
        <MetricCard label="Cost" value={`$${current_metrics.total_cost_usd.toFixed(4)}`} />
        <MetricCard label="Errors" value={current_metrics.total_errors} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <MetricCard
          label="Cache Hit Rate"
          value={`${performance_trends.cache_hit_rate_percent.toFixed(1)}%`}
        />
        <MetricCard
          label="Error Rate"
          value={`${performance_trends.error_rate_percent.toFixed(1)}%`}
        />
      </div>
    </Card>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
