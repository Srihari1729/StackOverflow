interface CardFaceProps {
  value: string;
  hidden?: boolean;
}

const suitColorMap: Record<string, string> = {
  s: 'var(--card-spade)',
  c: 'var(--card-club)',
  h: 'var(--card-heart)',
  d: 'var(--card-diamond)',
};

export function CardFace({ value, hidden = false }: CardFaceProps) {
  if (hidden || value === 'XX') {
    return <div className="card-face card-back" aria-label="Face down card" />;
  }

  const rank = value.slice(0, -1);
  const suit = value.slice(-1);
  const displaySuit = { s: '♠', c: '♣', h: '♥', d: '♦' }[suit] ?? suit;

  return (
    <div className="card-face" style={{ color: suitColorMap[suit] ?? 'var(--color-text)' }}>
      <span>{rank}</span>
      <strong>{displaySuit}</strong>
    </div>
  );
}
