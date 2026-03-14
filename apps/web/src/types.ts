export type DeckStyle = 'four_color' | 'standard';
export type Difficulty = 'easy' | 'medium' | 'hard';

export interface Profile {
  id: string;
  displayName: string;
  avatarSeed: string;
  avatarTone: string;
}

export interface RoomConfig {
  roomCode: string;
  seats: number;
  bots: number;
  difficulty: Difficulty;
  smallBlind: number;
  bigBlind: number;
}

export interface SeatView {
  seatIndex: number;
  name: string;
  stack: number;
  status: 'ready' | 'acting' | 'folded' | 'waiting';
  isBot: boolean;
  avatarSeed: string;
  avatarTone: string;
  cards?: [string, string];
}
