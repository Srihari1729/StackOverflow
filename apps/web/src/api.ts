import type { ActionType, RoomConfigInput, RoomState, RoomViewResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

interface SessionResponse {
  session_id: string;
  display_name: string;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? 'Request failed');
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.ok;
}

export async function createMockSession(displayName: string): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE_URL}/mock-auth/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ display_name: displayName }),
  });

  return parseResponse<SessionResponse>(response);
}

export async function createRoom(sessionId: string, config: RoomConfigInput): Promise<RoomState> {
  const response = await fetch(`${API_BASE_URL}/rooms`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      config: {
        max_seats: config.maxSeats,
        bot_count: config.botCount,
        small_blind: config.smallBlind,
        big_blind: config.bigBlind,
        starting_stack: config.startingStack,
        difficulty: config.difficulty,
      },
    }),
  });

  return parseResponse<RoomState>(response);
}

export async function joinRoom(sessionId: string, roomCode: string): Promise<RoomState> {
  const response = await fetch(`${API_BASE_URL}/rooms/join`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      room_code: roomCode.toUpperCase(),
    }),
  });

  return parseResponse<RoomState>(response);
}

export async function getRoom(roomCode: string, sessionId: string): Promise<RoomViewResponse> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomCode}?session_id=${encodeURIComponent(sessionId)}`);
  return parseResponse<RoomViewResponse>(response);
}

export async function startHand(roomCode: string, sessionId: string): Promise<RoomState> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomCode}/start?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });

  return parseResponse<RoomState>(response);
}

export async function sendAction(
  roomCode: string,
  sessionId: string,
  action: ActionType,
  amount = 0,
): Promise<RoomState> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomCode}/actions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      action,
      amount,
    }),
  });

  return parseResponse<RoomState>(response);
}
