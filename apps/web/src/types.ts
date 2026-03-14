export type DeckStyle = 'four_color' | 'standard';
export type Difficulty = 'easy' | 'medium' | 'hard';
export type RoomStatus = 'lobby' | 'active' | 'hand_over';
export type SeatStatus = 'active' | 'folded' | 'all_in' | 'waiting' | 'busted';
export type ActionType = 'fold' | 'check' | 'call' | 'raise' | 'all_in';

export interface RoomConfigInput {
  maxSeats: number;
  botCount: number;
  smallBlind: number;
  bigBlind: number;
  startingStack: number;
  difficulty: Difficulty;
}

export interface BotProfile {
  difficulty: Difficulty;
  personality: string;
  avatar_seed: string;
  avatar_tone: string;
}

export interface SeatState {
  seat_index: number;
  occupant_id: string | null;
  occupant_name: string;
  occupant_type: 'human' | 'bot' | null;
  avatar_seed: string;
  avatar_tone: string;
  stack: number;
  status: SeatStatus;
  hole_cards: string[];
  current_bet: number;
  total_committed: number;
  is_dealer: boolean;
  is_small_blind: boolean;
  is_big_blind: boolean;
  bot_profile: BotProfile | null;
}

export interface ActionRecord {
  order: number;
  seat_index: number;
  actor_name: string;
  action: ActionType;
  amount: number;
  target_bet: number;
  street: string;
  note: string;
}

export interface PotState {
  amount: number;
  eligible_seat_indices: number[];
}

export interface HandState {
  hand_id: string;
  hand_number: number;
  street: string;
  dealer_seat: number;
  small_blind_seat: number;
  big_blind_seat: number;
  acting_seat: number | null;
  board: string[];
  pot_total: number;
  current_bet: number;
  min_raise_to: number;
  pending_to_act: number[];
  action_log: ActionRecord[];
  winner_text: string;
  winning_seat_indices: number[];
  pots: PotState[];
  completed: boolean;
}

export interface RoomState {
  room_code: string;
  host_session_id: string;
  status: RoomStatus;
  config: {
    max_seats: number;
    bot_count: number;
    small_blind: number;
    big_blind: number;
    starting_stack: number;
    difficulty: Difficulty;
  };
  seats: SeatState[];
  hand_state: HandState | null;
  version: number;
}

export interface RoomViewResponse {
  room: RoomState;
  legal_actions: ActionType[];
}
