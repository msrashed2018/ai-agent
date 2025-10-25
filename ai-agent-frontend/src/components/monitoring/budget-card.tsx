'use client';

import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { BudgetStatusResponse } from '@/types/api';

interface BudgetCardProps {
  budget: BudgetStatusResponse | undefined;
  isLoading: boolean;
}

export function BudgetCard({
  budget,
  isLoading,
}: BudgetCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">Budget Status</h3>
        <div className="space-y-3">
          <div className="animate-pulse h-8 bg-gray-200 rounded w-1/3" />
          <div className="animate-pulse h-4 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (!budget) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">Budget Status</h3>
        <p className="text-sm text-gray-500">No budget data available</p>
      </div>
    );
  }

  const percentUsed = budget.budget_limit > 0 ? ((budget.current_usage / budget.budget_limit) * 100) : 0;
  const remaining = budget.remaining;

  let statusColor = 'text-green-600';
  let bgColor = 'bg-green-50';
  let borderColor = 'border-green-200';
  let Icon = CheckCircle2;

  if (percentUsed >= 90) {
    statusColor = 'text-red-600';
    bgColor = 'bg-red-50';
    borderColor = 'border-red-200';
    Icon = AlertCircle;
  } else if (percentUsed >= 75) {
    statusColor = 'text-yellow-600';
    bgColor = 'bg-yellow-50';
    borderColor = 'border-yellow-200';
    Icon = AlertTriangle;
  }

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} p-6`}>
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Budget Status</h3>
        <Icon className={`h-6 w-6 ${statusColor}`} />
      </div>

      <div className="space-y-4">
        {/* Budget Overview */}
        <div>
          <div className="flex justify-between items-baseline mb-2">
            <span className="text-sm text-gray-600">Budget Status</span>
            <span className="text-2xl font-bold text-gray-900">
              ${budget.current_usage.toFixed(2)} / ${budget.budget_limit.toFixed(2)}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                percentUsed >= 90
                  ? 'bg-red-600'
                  : percentUsed >= 75
                  ? 'bg-yellow-600'
                  : 'bg-green-600'
              }`}
              style={{ width: `${Math.min(percentUsed, 100)}%` }}
            />
          </div>

          <div className="mt-2 flex justify-between text-sm">
            <span className="text-gray-600">Used: {percentUsed.toFixed(1)}%</span>
            <span className={statusColor}>Remaining: ${remaining.toFixed(2)}</span>
          </div>
        </div>

        {/* Warnings */}
        {percentUsed >= 75 && (
          <div className={`p-3 rounded-lg ${percentUsed >= 90 ? 'bg-red-100' : 'bg-yellow-100'}`}>
            <p className={`text-sm font-medium ${percentUsed >= 90 ? 'text-red-800' : 'text-yellow-800'}`}>
              {percentUsed >= 90
                ? '⚠️ Budget limit nearly reached! Consider reviewing your usage.'
                : '⚠️ Budget usage is high. Monitor your spending.'}
            </p>
          </div>
        )}

        {/* Budget Period */}
        {budget.period && (
          <div className="text-sm text-gray-600">
            <p>Period: {budget.period}</p>
          </div>
        )}
      </div>
    </div>
  );
}
