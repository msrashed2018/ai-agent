'use client';

import * as React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';
import { SessionResponse } from '@/types/api';
import { MessageSquare, Wrench, DollarSign, Clock } from 'lucide-react';

interface SessionStatsProps {
  session: SessionResponse;
}

export function SessionStats({ session }: SessionStatsProps) {
  const stats = [
    {
      icon: MessageSquare,
      label: 'Messages',
      value: session.message_count,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      icon: Wrench,
      label: 'Tool Calls',
      value: session.tool_call_count,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
    {
      icon: DollarSign,
      label: 'Total Cost',
      value: session.total_cost_usd ? formatCurrency(session.total_cost_usd) : '-',
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      icon: Clock,
      label: 'Status',
      value: session.status,
      color: 'text-gray-600',
      bg: 'bg-gray-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${stat.bg}`}>
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-xl font-semibold mt-1">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
