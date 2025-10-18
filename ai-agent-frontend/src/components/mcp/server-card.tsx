import { MCPServerResponse } from '@/types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { HealthBadge } from './health-badge';
import { Edit, Trash2, Activity, Globe } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { getTypeBgColor, getTypeColor } from './type-selector';
import { cn } from '@/lib/utils';

interface ServerCardProps {
  server: MCPServerResponse;
  onEdit: (server: MCPServerResponse) => void;
  onDelete: (serverId: string) => void;
  onHealthCheck: (serverId: string) => void;
  onToggleEnabled: (serverId: string, enabled: boolean) => void;
}

export function ServerCard({
  server,
  onEdit,
  onDelete,
  onHealthCheck,
  onToggleEnabled,
}: ServerCardProps) {
  const isReadOnly = server.is_global;

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg">{server.name}</CardTitle>
              {server.is_global && (
                <Badge variant="secondary" className="text-xs">
                  <Globe className="h-3 w-3 mr-1" />
                  Global
                </Badge>
              )}
            </div>
            {server.description && (
              <CardDescription className="line-clamp-2">{server.description}</CardDescription>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={server.is_enabled}
              onCheckedChange={(checked) => onToggleEnabled(server.id, checked)}
              disabled={isReadOnly}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Type and Health */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Badge
              variant="secondary"
              className={cn('gap-1', getTypeBgColor(server.server_type))}
            >
              <span className={cn('font-medium', getTypeColor(server.server_type))}>
                {server.server_type.toUpperCase()}
              </span>
            </Badge>
          </div>
          <HealthBadge status={server.health_status} />
        </div>

        {/* Config Preview */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-medium text-gray-500 mb-2">Configuration</div>
          {server.server_type === 'stdio' && server.config.command && (
            <div className="space-y-1">
              <div className="text-sm">
                <span className="text-gray-600">Command:</span>{' '}
                <code className="text-xs bg-white px-1.5 py-0.5 rounded">
                  {server.config.command}
                </code>
              </div>
              {server.config.args && server.config.args.length > 0 && (
                <div className="text-sm text-gray-600">
                  Args: {server.config.args.length} parameter(s)
                </div>
              )}
            </div>
          )}
          {(server.server_type === 'sse' || server.server_type === 'http') && server.config.url && (
            <div className="text-sm">
              <span className="text-gray-600">URL:</span>{' '}
              <code className="text-xs bg-white px-1.5 py-0.5 rounded break-all">
                {server.config.url}
              </code>
            </div>
          )}
        </div>

        {/* Last Health Check */}
        {server.last_health_check_at && (
          <div className="text-xs text-gray-500">
            Last checked: {new Date(server.last_health_check_at).toLocaleString()}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onHealthCheck(server.id)}
            className="flex-1"
          >
            <Activity className="h-4 w-4 mr-1" />
            Health Check
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(server)}
            disabled={isReadOnly}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(server.id)}
            disabled={isReadOnly}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
