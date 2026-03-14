import type { SeatView } from '../types';
import { CardFace } from './CardFace';

interface SeatProps {
  seat: SeatView;
}

export function Seat({ seat }: SeatProps) {
  return (
    <article className={`seat seat-${seat.status}`}>
      <div className="seat-topline">
        <div
          className="seat-avatar"
          aria-hidden="true"
          style={{ background: seat.avatarTone }}
        >
          {seat.avatarSeed}
        </div>

        <div>
          <div className="seat-name-row">
            <h3>{seat.name}</h3>
            {seat.isBot ? <span className="seat-pill">Bot</span> : <span className="seat-pill human">You</span>}
          </div>
          <p className="muted">${seat.stack}</p>
        </div>
      </div>

      <div className="seat-cards">
        {seat.cards ? (
          seat.cards.map((card) => <CardFace key={card} value={card} />)
        ) : (
          <>
            <CardFace value="?" hidden />
            <CardFace value="?" hidden />
          </>
        )}
      </div>
    </article>
  );
}
