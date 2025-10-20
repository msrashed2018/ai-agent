'use client';

import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { ConnectionStatus } from '@/types/websocket';

interface ConnectionStatusProps {
  status: ConnectionStatus;
  onReconnect?: () => void;
}

export function ConnectionStatusBadge({ status, onReconnect }: ConnectionStatusProps) {
  const statusConfig = {
    connected: {
      icon: Wifi,
      label: 'Connected',
      variant: 'default' as const,
      className: 'bg-green-500 hover:bg-green-600',
    },
    connecting: {
      icon: Loader2,
      label: 'Connecting...',
      variant: 'secondary' as const,
      className: 'bg-yellow-500 hover:bg-yellow-600',
    },
    disconnected: {
      icon: WifiOff,
      label: 'Disconnected',
      variant: 'destructive' as const,
      className: '',
    },
    error: {
      icon: WifiOff,
      label: 'Connection Error',
      variant: 'destructive' as const,
      className: '',
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2">
      <Badge variant={config.variant} className={config.className}>
        <Icon className={`mr-1 h-3 w-3 ${status === 'connecting' ? 'animate-spin' : ''}`} />
        {config.label}
      </Badge>
      {(status === 'disconnected' || status === 'error') && onReconnect && (
        <Button
          size="sm"
          variant="outline"
          onClick={onReconnect}
          className="h-6 text-xs"
        >
          Reconnect
        </Button>
      )}
    </div>
  );
}

export function ConnectionStatusIndicator({ status }: { status: ConnectionStatus }) {
  const statusConfig = {
    connected: {
      color: 'bg-green-500',
      pulse: true,
      tooltip: 'Real-time updates active',
    },
    connecting: {
      color: 'bg-yellow-500',
      pulse: true,
      tooltip: 'Connecting...',
    },
    disconnected: {
      color: 'bg-gray-400',
      pulse: false,
      tooltip: 'No real-time connection',
    },
    error: {
      color: 'bg-red-500',
      pulse: false,
      tooltip: 'Connection error',
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2" title={config.tooltip}>
      <div className="relative">
        <div className={`h-2 w-2 rounded-full ${config.color}`} />
        {config.pulse && (
          <div className={`absolute inset-0 h-2 w-2 rounded-full ${config.color} animate-ping opacity-75`} />
        )}
      </div>
      <span className="text-xs text-muted-foreground">{config.tooltip}</span>
    </div>
  );
}
