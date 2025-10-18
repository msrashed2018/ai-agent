'use client';

import * as React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { SessionStats } from '@/components/sessions/session-stats';
import { MessageBubble } from '@/components/sessions/message-bubble';
import { ToolCallCard } from '@/components/sessions/tool-call-card';
import {
  useSession,
  useSessionMessages,
  useSessionToolCalls,
  usePauseSession,
  useResumeSession,
  useDownloadWorkdir,
} from '@/hooks/use-sessions';
import {
  MessageSquare,
  Pause,
  Play,
  Download,
  ArrowLeft,
  Settings,
} from 'lucide-react';
import { formatDate, getStatusColor } from '@/lib/utils';

export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const { data: session, isLoading: sessionLoading } = useSession(sessionId);
  const { data: messages, isLoading: messagesLoading } = useSessionMessages(sessionId);
  const { data: toolCalls, isLoading: toolCallsLoading } = useSessionToolCalls(sessionId);

  const pauseSession = usePauseSession();
  const resumeSession = useResumeSession();
  const downloadWorkdir = useDownloadWorkdir();

  if (sessionLoading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
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

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => router.push('/sessions')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">
                {session.name || `Session ${session.id.substring(0, 8)}`}
              </h1>
              <Badge className={getStatusColor(session.status)}>{session.status}</Badge>
            </div>
            {session.description && (
              <p className="text-gray-500 mt-1">{session.description}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/sessions/${session.id}/query`)}
            disabled={session.status === 'completed' || session.status === 'failed'}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Query
          </Button>

          {session.status === 'active' && (
            <Button
              variant="outline"
              onClick={() => pauseSession.mutate(session.id)}
              disabled={pauseSession.isPending}
            >
              <Pause className="h-4 w-4 mr-2" />
              Pause
            </Button>
          )}

          {session.status === 'paused' && (
            <Button
              variant="outline"
              onClick={() => resumeSession.mutate({ sessionId: session.id })}
              disabled={resumeSession.isPending}
            >
              <Play className="h-4 w-4 mr-2" />
              Resume
            </Button>
          )}

          <Button
            variant="outline"
            onClick={() => downloadWorkdir.mutate(session.id)}
            disabled={downloadWorkdir.isPending}
          >
            <Download className="h-4 w-4 mr-2" />
            {downloadWorkdir.isPending ? 'Downloading...' : 'Download Workdir'}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <SessionStats session={session} />

      {/* Tabs */}
      <Tabs defaultValue="messages" className="space-y-4">
        <TabsList>
          <TabsTrigger value="messages">
            Messages ({session.message_count})
          </TabsTrigger>
          <TabsTrigger value="tool-calls">
            Tool Calls ({session.tool_call_count})
          </TabsTrigger>
          <TabsTrigger value="configuration">
            <Settings className="h-4 w-4 mr-2" />
            Configuration
          </TabsTrigger>
        </TabsList>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Messages</CardTitle>
            </CardHeader>
            <CardContent>
              {messagesLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : messages && messages.length > 0 ? (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">
                  No messages yet. Start a conversation by querying this session.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tool Calls Tab */}
        <TabsContent value="tool-calls" className="space-y-4">
          {toolCallsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : toolCalls && toolCalls.length > 0 ? (
            <div className="space-y-4">
              {toolCalls.map((toolCall) => (
                <ToolCallCard key={toolCall.id} toolCall={toolCall} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-8">
                <p className="text-center text-gray-500">
                  No tool calls yet. Tool calls will appear here when the agent uses tools.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Session Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Session ID</p>
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded mt-1 block">
                    {session.id}
                  </code>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">User ID</p>
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded mt-1 block">
                    {session.user_id}
                  </code>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Created</p>
                  <p className="text-sm mt-1">{formatDate(session.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Last Updated</p>
                  <p className="text-sm mt-1">{formatDate(session.updated_at)}</p>
                </div>
              </div>

              {/* Working Directory */}
              <div>
                <p className="text-sm font-medium text-gray-500">Working Directory</p>
                <code className="text-sm bg-gray-100 px-2 py-1 rounded mt-1 block">
                  {session.working_directory}
                </code>
              </div>

              {/* SDK Options */}
              <div>
                <p className="text-sm font-medium text-gray-500 mb-2">SDK Options</p>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">
                  {JSON.stringify(session.sdk_options, null, 2)}
                </pre>
              </div>

              {/* Allowed Tools */}
              <div>
                <p className="text-sm font-medium text-gray-500 mb-2">Allowed Tools</p>
                {session.allowed_tools.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {session.allowed_tools.map((tool) => (
                      <Badge key={tool} variant="outline">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">All tools allowed</p>
                )}
              </div>

              {/* System Prompt */}
              {session.system_prompt && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">System Prompt</p>
                  <div className="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
                    {session.system_prompt}
                  </div>
                </div>
              )}

              {/* Parent Session */}
              {session.parent_session_id && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Parent Session</p>
                  <Button
                    variant="link"
                    className="px-0 h-auto"
                    onClick={() => router.push(`/sessions/${session.parent_session_id}`)}
                  >
                    {session.parent_session_id}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
