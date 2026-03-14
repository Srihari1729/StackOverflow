import type { Difficulty } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

interface SessionResponse {
  session_id: string;
  display_name: string;
}

interface CreateRoomResponse {
  room_code: string;
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

  if (!response.ok) {
    throw new Error('Failed to create mock session');
  }

  return response.json();
}

export async function createRoom(sessionId: string, difficulty: Difficulty): Promise<CreateRoomResponse> {
  const response = await fetch(`${API_BASE_URL}/rooms`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      config: {
        max_seats: 6,
        bot_count: 4,
        small_blind: 10,
        big_blind: 20,
        difficulty,
      },
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create room');
  }

  return response.json();
}
