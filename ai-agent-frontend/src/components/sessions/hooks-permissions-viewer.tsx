'use client';

import { useSessionHooks, useSessionPermissions } from '@/hooks/use-sessions';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

interface HooksPermissionsViewerProps {
  sessionId: string;
}

export function HooksPermissionsViewer({ sessionId }: HooksPermissionsViewerProps) {
  const { data: hooks, isLoading: hooksLoading } = useSessionHooks(sessionId);
  const { data: permissions, isLoading: permissionsLoading } = useSessionPermissions(sessionId);

  return (
    <Card className="p-6">
      <Tabs defaultValue="hooks">
        <TabsList>
          <TabsTrigger value="hooks">Hooks ({hooks?.length || 0})</TabsTrigger>
          <TabsTrigger value="permissions">Permissions ({permissions?.length || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="hooks" className="space-y-2">
          {hooksLoading ? (
            <p>Loading hooks...</p>
          ) : hooks && hooks.length > 0 ? (
            hooks.map((hook) => (
              <div key={hook.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <Badge variant="outline">{hook.hook_type}</Badge>
                    <p className="font-medium mt-1">{hook.hook_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(hook.executed_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={hook.continue_execution ? 'default' : 'destructive'}>
                    {hook.continue_execution ? 'Continued' : 'Blocked'}
                  </Badge>
                </div>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No hooks executed yet</p>
          )}
        </TabsContent>

        <TabsContent value="permissions" className="space-y-2">
          {permissionsLoading ? (
            <p>Loading permissions...</p>
          ) : permissions && permissions.length > 0 ? (
            permissions.map((perm) => (
              <div key={perm.id} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{perm.tool_name}</p>
                    {perm.reason && (
                      <p className="text-xs text-muted-foreground mt-1">{perm.reason}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {new Date(perm.decided_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={perm.decision === 'allow' ? 'default' : 'destructive'}>
                    {perm.decision}
                  </Badge>
                </div>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No permission decisions yet</p>
          )}
        </TabsContent>
      </Tabs>
    </Card>
  );
}
