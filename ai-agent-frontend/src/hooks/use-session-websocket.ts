import { useEffect, useCallback, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getWebSocketURL, parseWebSocketMessage, isWebSocketSupported } from '@/lib/websocket-client';
import { sessionKeys } from './use-sessions';
import type {
  ServerMessage,
  ClientMessage,
  ConnectionStatus,
  WebSocketOptions,
} from '@/types/websocket';
import {
  isConnectedMessage,
  isMessageReceivedMessage,
  isStatusChangeMessage,
  isToolCallStartedMessage,
  isToolCallCompletedMessage,
  isErrorMessage,
} from '@/types/websocket';

/**
 * Custom hook for WebSocket connection to a session
 * Provides real-time updates for messages, tool calls, and session status
 */
export function useSessionWebSocket(
  sessionId: string | undefined,
  options: WebSocketOptions = {}
) {
  const {
    enabled = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    onConnected,
    onDisconnected,
    onError,
  } = options;

  const queryClient = useQueryClient();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Get WebSocket URL
  const socketUrl = sessionId && enabled && isWebSocketSupported()
    ? getWebSocketURL(sessionId)
    : null;

  // Setup WebSocket connection
  const {
    sendJsonMessage,
    lastJsonMessage,
    readyState,
    getWebSocket,
  } = useWebSocket(socketUrl, {
    shouldReconnect: () => enabled && !!sessionId,
    reconnectAttempts,
    reconnectInterval,
    onOpen: () => {
      console.log(`WebSocket connected to session ${sessionId}`);
      onConnected?.();

      // Start heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      heartbeatIntervalRef.current = setInterval(() => {
        sendJsonMessage({ type: 'ping' } as ClientMessage);
      }, heartbeatInterval);
    },
    onClose: () => {
      console.log(`WebSocket disconnected from session ${sessionId}`);
      onDisconnected?.();

      // Stop heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
    },
    onError: (event) => {
      console.error('WebSocket error:', event);
      const error = new Error('WebSocket connection error');
      onError?.(error);
      toast.error('Real-time connection error. Retrying...');
    },
  });

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastJsonMessage || !sessionId) return;

    const message = lastJsonMessage as ServerMessage;

    try {
      // Handle different message types
      if (isConnectedMessage(message)) {
        console.log('WebSocket connection confirmed:', message.data);
        toast.success('Connected to real-time session updates');
      }
      else if (isMessageReceivedMessage(message)) {
        // Invalidate messages query to fetch new message
        queryClient.invalidateQueries({ queryKey: sessionKeys.messages(sessionId) });
        queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) });
      }
      else if (isStatusChangeMessage(message)) {
        // Update session status in cache
        queryClient.setQueryData(sessionKeys.detail(sessionId), (old: any) => {
          if (!old) return old;
          return { ...old, status: message.data.status };
        });
        queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) });
      }
      else if (isToolCallStartedMessage(message)) {
        // Invalidate tool calls to show new tool call
        queryClient.invalidateQueries({ queryKey: sessionKeys.toolCalls(sessionId) });
        toast.info(`Tool "${message.data.tool_name}" started`);
      }
      else if (isToolCallCompletedMessage(message)) {
        // Invalidate tool calls to update tool call status
        queryClient.invalidateQueries({ queryKey: sessionKeys.toolCalls(sessionId) });

        if (message.data.status === 'completed') {
          toast.success(`Tool "${message.data.tool_name}" completed`);
        } else if (message.data.status === 'failed') {
          toast.error(`Tool "${message.data.tool_name}" failed`);
        }
      }
      else if (isErrorMessage(message)) {
        console.error('WebSocket error message:', message.data);
        toast.error(message.data.message || 'An error occurred');
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }, [lastJsonMessage, sessionId, queryClient]);

  // Cleanup heartbeat on unmount
  useEffect(() => {
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, []);

  // Send query message to session
  const sendQuery = useCallback((message: string) => {
    if (readyState === ReadyState.OPEN) {
      sendJsonMessage({ type: 'query', message } as ClientMessage);
    } else {
      toast.error('Not connected to real-time session');
    }
  }, [readyState, sendJsonMessage]);

  // Map ReadyState to ConnectionStatus
  const connectionStatus: ConnectionStatus = {
    [ReadyState.CONNECTING]: 'connecting',
    [ReadyState.OPEN]: 'connected',
    [ReadyState.CLOSING]: 'disconnected',
    [ReadyState.CLOSED]: 'disconnected',
    [ReadyState.UNINSTANTIATED]: 'disconnected',
  }[readyState] as ConnectionStatus;

  return {
    sendQuery,
    connectionStatus,
    isConnected: readyState === ReadyState.OPEN,
    isConnecting: readyState === ReadyState.CONNECTING,
    getWebSocket,
  };
}
