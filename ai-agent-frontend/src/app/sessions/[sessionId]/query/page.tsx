'use client';

import * as React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageBubble } from '@/components/sessions/message-bubble';
import { ToolCallCard } from '@/components/sessions/tool-call-card';
import {
  useSession,
  useSessionMessages,
  useQuerySession,
  useSessionToolCalls,
} from '@/hooks/use-sessions';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { getStatusColor } from '@/lib/utils';

export default function SessionQueryPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [message, setMessage] = React.useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const { data: session, isLoading: sessionLoading } = useSession(sessionId);
  const { data: messages, isLoading: messagesLoading } = useSessionMessages(sessionId);
  const { data: toolCalls } = useSessionToolCalls(sessionId);

  const querySession = useQuerySession(sessionId);

  // Auto-scroll to bottom when messages update
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || querySession.isPending) return;

    const userMessage = message;
    setMessage('');

    try {
      await querySession.mutateAsync({ message: userMessage });
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (sessionLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Session not found
        </div>
      </div>
    );
  }

  const canQuery =
    session.status === 'active' || session.status === 'paused' || session.status === 'initializing';

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="border-b bg-white sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => router.push(`/sessions/${sessionId}`)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-bold">
                    {session.name || `Session ${session.id.substring(0, 8)}`}
                  </h1>
                  <Badge className={getStatusColor(session.status)}>{session.status}</Badge>
                </div>
                <p className="text-sm text-gray-500">
                  Chat with your AI agent
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="container mx-auto px-4 py-6">
          {messagesLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-3/4" />
              <Skeleton className="h-20 w-3/4 ml-auto" />
              <Skeleton className="h-20 w-3/4" />
            </div>
          ) : messages && messages.length > 0 ? (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((msg, index) => {
                // Find tool calls related to this message
                const relatedToolCalls = toolCalls?.filter(
                  (tc) => tc.message_id === msg.id
                );

                return (
                  <div key={msg.id}>
                    <MessageBubble message={msg} />

                    {/* Show tool calls inline if they exist for this message */}
                    {relatedToolCalls && relatedToolCalls.length > 0 && (
                      <div className="ml-12 mt-2 space-y-2">
                        {relatedToolCalls.map((toolCall) => (
                          <ToolCallCard key={toolCall.id} toolCall={toolCall} />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}

              {querySession.isPending && (
                <div className="flex items-center gap-3 text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Agent is thinking...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <Card className="max-w-md">
                <CardContent className="py-8 text-center">
                  <p className="text-gray-500">
                    No messages yet. Start a conversation by typing a message below.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-white sticky bottom-0">
        <div className="container mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <Textarea
                placeholder={
                  canQuery
                    ? 'Type your message... (Shift+Enter for new line)'
                    : 'Session is not active'
                }
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={!canQuery || querySession.isPending}
                rows={3}
                className="resize-none"
              />
              <Button
                type="submit"
                disabled={!canQuery || !message.trim() || querySession.isPending}
                className="self-end"
              >
                {querySession.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>

            {!canQuery && (
              <p className="text-sm text-red-500 mt-2">
                This session is {session.status} and cannot accept new messages.
                {session.status === 'paused' && ' Resume the session to continue.'}
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
