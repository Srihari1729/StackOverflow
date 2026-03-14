import type { SeatState } from '../types';
import { CardFace } from './CardFace';

interface SeatProps {
  seat: SeatState;
  isViewer: boolean;
}

export function Seat({ seat, isViewer }: SeatProps) {
  const badges = [
    seat.is_dealer ? 'D' : null,
    seat.is_small_blind ? 'SB' : null,
    seat.is_big_blind ? 'BB' : null,
  ].filter(Boolean);

  return (
    <article className={`seat seat-${seat.status}`}>
      <div className="seat-topline">
        <div className="seat-avatar" aria-hidden="true" style={{ background: seat.avatar_tone }}>
          {seat.avatar_seed}
        </div>

        <div>
          <div className="seat-name-row">
            <h3>{seat.occupant_name}</h3>
            {seat.occupant_type === 'bot' ? (
              <span className="seat-pill">Bot</span>
            ) : seat.occupant_id ? (
              <span className="seat-pill human">{isViewer ? 'You' : 'Player'}</span>
            ) : null}
            {badges.map((badge) => (
              <span key={badge} className="seat-pill role-pill">
                {badge}
              </span>
            ))}
          </div>
          <p className="muted">
            ${seat.stack} {seat.current_bet > 0 ? `· Bet ${seat.current_bet}` : ''}
          </p>
        </div>
      </div>

      <div className="seat-cards">
        {seat.hole_cards.length > 0 ? (
          seat.hole_cards.map((card) => <CardFace key={`${seat.seat_index}-${card}`} value={card} hidden={card === 'XX'} />)
        ) : (
          <>
            <CardFace value="XX" hidden />
            <CardFace value="XX" hidden />
          </>
        )}
      </div>
    </article>
  );
}
