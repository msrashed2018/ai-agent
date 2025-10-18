'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';
import { MessageResponse } from '@/types/api';
import { Copy, Check, User, Bot } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MessageBubbleProps {
  message: MessageResponse;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        'flex w-full gap-3 mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
          <Bot className="h-4 w-4 text-gray-600" />
        </div>
      )}

      <div
        className={cn(
          'flex flex-col gap-1 max-w-[80%]',
          isUser && 'items-end'
        )}
      >
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="font-medium">
            {isUser ? 'You' : isAssistant ? 'Assistant' : 'System'}
          </span>
          <span>{formatDate(message.created_at)}</span>
        </div>

        <div
          className={cn(
            'rounded-lg px-4 py-3 text-sm relative group',
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          )}
        >
          <div className="whitespace-pre-wrap break-words">{message.content}</div>

          <Button
            variant="ghost"
            size="sm"
            className={cn(
              'absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity',
              isUser ? 'text-white hover:bg-blue-700' : 'text-gray-600 hover:bg-gray-200'
            )}
            onClick={handleCopy}
          >
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          </Button>
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          <User className="h-4 w-4 text-white" />
        </div>
      )}
    </div>
  );
}
