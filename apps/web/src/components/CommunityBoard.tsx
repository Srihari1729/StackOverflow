import { CardFace } from './CardFace';

const boardCards = ['Q♣', 'J♥', '9♦', '3♠', '3♣'];

export function CommunityBoard() {
  return (
    <section className="board-panel">
      <div className="board-copy">
        <p className="eyebrow">Hand in progress</p>
        <h2>River. Pot 540.</h2>
        <p className="muted">
          Clean, deliberate table state with the acting player centered in the flow.
        </p>
      </div>

      <div className="board-cards" aria-label="Community cards">
        {boardCards.map((card) => (
          <CardFace key={card} value={card} />
        ))}
      </div>
    </section>
  );
}
