interface CardFaceProps {
  value: string;
  hidden?: boolean;
}

const suitColorMap: Record<string, string> = {
  '♠': 'var(--card-spade)',
  '♣': 'var(--card-club)',
  '♥': 'var(--card-heart)',
  '♦': 'var(--card-diamond)',
};

export function CardFace({ value, hidden = false }: CardFaceProps) {
  if (hidden) {
    return <div className="card-face card-back" aria-label="Face down card" />;
  }

  const rank = value.slice(0, -1);
  const suit = value.slice(-1);

  return (
    <div className="card-face" style={{ color: suitColorMap[suit] ?? 'var(--color-text)' }}>
      <span>{rank}</span>
      <strong>{suit}</strong>
    </div>
  );
}
