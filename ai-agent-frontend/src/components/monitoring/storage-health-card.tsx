'use client';

import { HardDrive, AlertCircle } from 'lucide-react';
import type { StorageHealthResponse } from '@/types/api';

interface StorageHealthCardProps {
  storage: StorageHealthResponse | undefined;
  isLoading: boolean;
  error?: Error | null;
}

export function StorageHealthCard({
  storage,
  isLoading,
  error,
}: StorageHealthCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">Storage</h3>
        <div className="space-y-3">
          <div className="animate-pulse h-8 bg-gray-200 rounded w-1/3" />
          <div className="animate-pulse h-4 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold text-red-900">Storage</h3>
            <p className="text-sm text-red-700 mt-1">Failed to load storage info</p>
          </div>
        </div>
      </div>
    );
  }

  if (!storage) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">Storage</h3>
        <p className="text-sm text-gray-500">No storage data available</p>
      </div>
    );
  }

  const usedPercent = storage.disk_usage_percent || 0;
  const isWarning = usedPercent >= 80;

  return (
    <div className={`rounded-lg border ${isWarning ? 'border-yellow-200 bg-yellow-50' : 'border-gray-200 bg-white'} p-6`}>
      <div className="flex items-start justify-between mb-4">
        <h3 className={`text-lg font-semibold ${isWarning ? 'text-yellow-900' : 'text-gray-900'}`}>
          Storage
        </h3>
        <div className={`rounded-lg ${isWarning ? 'bg-yellow-100' : 'bg-blue-100'} p-3`}>
          <HardDrive className={`h-6 w-6 ${isWarning ? 'text-yellow-600' : 'text-blue-600'}`} />
        </div>
      </div>

      <div className="space-y-4">
        {/* Usage Display */}
        <div>
          <div className="flex justify-between items-baseline mb-2">
            <span className="text-sm text-gray-600">Disk Usage</span>
            <span className={`text-2xl font-bold ${isWarning ? 'text-yellow-900' : 'text-gray-900'}`}>
              {usedPercent.toFixed(1)}%
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                usedPercent >= 90
                  ? 'bg-red-600'
                  : usedPercent >= 80
                  ? 'bg-yellow-600'
                  : 'bg-green-600'
              }`}
              style={{ width: `${Math.min(usedPercent, 100)}%` }}
            />
          </div>

          <div className="mt-2 flex justify-between text-sm">
            <span className={isWarning ? 'text-yellow-700' : 'text-gray-600'}>
              Status: {storage.status}
            </span>
            <span className="text-gray-600">
              {storage.storage_available ? 'Available' : 'Not Available'}
            </span>
          </div>
        </div>

        {/* Warning */}
        {isWarning && (
          <div className="p-3 rounded-lg bg-yellow-100">
            <p className="text-sm font-medium text-yellow-800">
              ⚠️ Storage usage is high. Consider cleaning up old files or increasing capacity.
            </p>
          </div>
        )}

        {/* Message */}
        {storage.message && (
          <div className="text-sm text-gray-600">
            <p>{storage.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
