'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate, getStatusColor } from '@/lib/utils';
import { ToolCallResponse } from '@/types/api';
import { ChevronDown, ChevronRight, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ToolCallCardProps {
  toolCall: ToolCallResponse;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 flex-1">
            <Wrench className="h-4 w-4 text-gray-500" />
            <CardTitle className="text-sm font-medium">{toolCall.tool_name}</CardTitle>
            <Badge className={getStatusColor(toolCall.status)}>{toolCall.status}</Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {formatDate(toolCall.created_at)}
          {toolCall.completed_at && ` - ${formatDate(toolCall.completed_at)}`}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 space-y-4">
          {/* Input */}
          <div>
            <h4 className="text-sm font-medium mb-2">Input</h4>
            <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-60">
              {JSON.stringify(toolCall.tool_input, null, 2)}
            </pre>
          </div>

          {/* Output */}
          {toolCall.tool_output && (
            <div>
              <h4 className="text-sm font-medium mb-2">Output</h4>
              <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-60">
                {JSON.stringify(toolCall.tool_output, null, 2)}
              </pre>
            </div>
          )}

          {/* Error */}
          {toolCall.error_message && (
            <div>
              <h4 className="text-sm font-medium mb-2 text-red-600">Error</h4>
              <div className="bg-red-50 border border-red-200 p-3 rounded text-xs text-red-800">
                {toolCall.error_message}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
