import type { Profile, RoomConfig, SeatView } from './types';

export const hostProfile: Profile = {
  id: 'user_srihari',
  displayName: 'Srihari',
  avatarSeed: 'SH',
  avatarTone: '#3f7cff',
};

export const defaultRoomConfig: RoomConfig = {
  roomCode: 'AB12CD',
  seats: 6,
  bots: 4,
  difficulty: 'medium',
  smallBlind: 10,
  bigBlind: 20,
};

export const createMockSeats = (profile: Profile): SeatView[] => [
  {
    seatIndex: 0,
    name: profile.displayName,
    stack: 2000,
    status: 'acting',
    isBot: false,
    avatarSeed: profile.avatarSeed,
    avatarTone: profile.avatarTone,
    cards: ['A♠', 'K♦'],
  },
  {
    seatIndex: 1,
    name: 'Pixel Shark',
    stack: 1840,
    status: 'ready',
    isBot: true,
    avatarSeed: 'PS',
    avatarTone: '#8b5cf6',
  },
  {
    seatIndex: 2,
    name: 'Loose Mango',
    stack: 1630,
    status: 'folded',
    isBot: true,
    avatarSeed: 'LM',
    avatarTone: '#f97316',
  },
  {
    seatIndex: 3,
    name: 'Trap Door',
    stack: 2260,
    status: 'waiting',
    isBot: true,
    avatarSeed: 'TD',
    avatarTone: '#22c55e',
  },
  {
    seatIndex: 4,
    name: 'Night River',
    stack: 1970,
    status: 'ready',
    isBot: true,
    avatarSeed: 'NR',
    avatarTone: '#ef4444',
  },
  {
    seatIndex: 5,
    name: 'Open Seat',
    stack: 0,
    status: 'waiting',
    isBot: false,
    avatarSeed: 'OS',
    avatarTone: '#475569',
  },
];
