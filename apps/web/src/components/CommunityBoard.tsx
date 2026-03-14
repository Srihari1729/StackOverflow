import type { HandState, RoomStatus } from '../types';
import { CardFace } from './CardFace';

interface CommunityBoardProps {
  handState: HandState | null;
  roomStatus: RoomStatus;
}

export function CommunityBoard({ handState, roomStatus }: CommunityBoardProps) {
  const boardCards = handState?.board ?? [];
  const streetLabel = handState?.street ?? roomStatus;

  return (
    <section className="board-panel">
      <div className="board-copy">
        <p className="eyebrow">Table state</p>
        <h2>
          {streetLabel.toUpperCase()}. Pot {handState?.pot_total ?? 0}.
        </h2>
        <p className="muted">
          {handState?.winner_text || 'Local-first table flow with authoritative backend state and hidden cards.'}
        </p>
      </div>

      <div className="board-cards" aria-label="Community cards">
        {boardCards.length === 0
          ? Array.from({ length: 5 }).map((_, index) => <CardFace key={index} value="XX" hidden />)
          : boardCards.map((card) => <CardFace key={card} value={card} />)}
      </div>
    </section>
  );
}
