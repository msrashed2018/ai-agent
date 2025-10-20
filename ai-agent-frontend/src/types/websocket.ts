import type { MessageResponse, ToolCallResponse, SessionStatus } from './api';

// ============================================================================
// WebSocket Message Types (Based on Backend Contract)
// ============================================================================

/**
 * Client to Server Messages
 */
export type ClientMessage = QueryMessage | PingMessage;

export interface QueryMessage {
  type: 'query';
  message: string;
}

export interface PingMessage {
  type: 'ping';
}

/**
 * Server to Client Messages
 */
export type ServerMessage =
  | ConnectedMessage
  | MessageReceivedMessage
  | MessageSentMessage
  | StatusChangeMessage
  | ToolCallStartedMessage
  | ToolCallCompletedMessage
  | ErrorMessage
  | PongMessage;

export interface ConnectedMessage {
  type: 'connected';
  data: {
    session_id: string;
  };
}

export interface MessageReceivedMessage {
  type: 'message';
  data: MessageResponse;
}

export interface MessageSentMessage {
  type: 'message_sent';
  data: {
    message_id: string;
  };
}

export interface StatusChangeMessage {
  type: 'status_change';
  data: {
    status: SessionStatus;
  };
}

export interface ToolCallStartedMessage {
  type: 'tool_call_started';
  data: ToolCallResponse;
}

export interface ToolCallCompletedMessage {
  type: 'tool_call_completed';
  data: ToolCallResponse;
}

export interface ErrorMessage {
  type: 'error';
  data: {
    code: string;
    message: string;
  };
}

export interface PongMessage {
  type: 'pong';
}

// ============================================================================
// WebSocket Connection Status
// ============================================================================

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// ============================================================================
// WebSocket Hook Options
// ============================================================================

export interface WebSocketOptions {
  enabled?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Error) => void;
}

// ============================================================================
// Type Guards
// ============================================================================

export function isConnectedMessage(msg: ServerMessage): msg is ConnectedMessage {
  return msg.type === 'connected';
}

export function isMessageReceivedMessage(msg: ServerMessage): msg is MessageReceivedMessage {
  return msg.type === 'message';
}

export function isMessageSentMessage(msg: ServerMessage): msg is MessageSentMessage {
  return msg.type === 'message_sent';
}

export function isStatusChangeMessage(msg: ServerMessage): msg is StatusChangeMessage {
  return msg.type === 'status_change';
}

export function isToolCallStartedMessage(msg: ServerMessage): msg is ToolCallStartedMessage {
  return msg.type === 'tool_call_started';
}

export function isToolCallCompletedMessage(msg: ServerMessage): msg is ToolCallCompletedMessage {
  return msg.type === 'tool_call_completed';
}

export function isErrorMessage(msg: ServerMessage): msg is ErrorMessage {
  return msg.type === 'error';
}

export function isPongMessage(msg: ServerMessage): msg is PongMessage {
  return msg.type === 'pong';
}
