'use client';

import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import type { CostSummaryResponse } from '@/types/api';

interface CostCardProps {
  title: string;
  costs: CostSummaryResponse | undefined;
  isLoading: boolean;
  period?: 'today' | 'week' | 'month';
}

export function CostCard({
  title,
  costs,
  isLoading,
  period = 'today',
}: CostCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="space-y-3">
          <div className="animate-pulse h-8 bg-gray-200 rounded w-1/3" />
          <div className="animate-pulse h-4 bg-gray-200 rounded w-2/3" />
        </div>
      </div>
    );
  }

  if (!costs) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <p className="text-sm text-gray-500">No cost data available</p>
      </div>
    );
  }

  const totalCost = costs.total_cost_usd || 0;
  const trend = 0; // No previous period data in API
  const percentChange = 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-2">{title}</p>
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold text-gray-900">
              ${totalCost.toFixed(2)}
            </div>
            <div className="flex items-center gap-1">
              {trend >= 0 ? (
                <TrendingUp className="h-4 w-4 text-red-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-green-600" />
              )}
              <span className={trend >= 0 ? 'text-red-600' : 'text-green-600'}>
                {trend >= 0 ? '+' : ''}{percentChange}%
              </span>
            </div>
          </div>
        </div>
        <div className="rounded-lg bg-blue-100 p-3">
          <DollarSign className="h-6 w-6 text-blue-600" />
        </div>
      </div>

      {costs.breakdown_by_model && Object.keys(costs.breakdown_by_model).length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Cost Breakdown by Model</h4>
          <dl className="space-y-2 text-sm">
            {Object.entries(costs.breakdown_by_model).map(([model, amount]) => (
              <div key={model} className="flex justify-between">
                <dt className="text-gray-600">{model}</dt>
                <dd className="font-medium text-gray-900">${amount.toFixed(2)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {(costs.session_count > 0 || costs.message_count > 0) && (
        <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Sessions:</span>
            <span>{costs.session_count}</span>
          </div>
          <div className="flex justify-between">
            <span>Messages:</span>
            <span>{costs.message_count}</span>
          </div>
          <div className="flex justify-between">
            <span>Avg per session:</span>
            <span>${costs.average_cost_per_session.toFixed(2)}</span>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500 mt-4">
        Period: {period.charAt(0).toUpperCase() + period.slice(1)}
      </p>
    </div>
  );
}
