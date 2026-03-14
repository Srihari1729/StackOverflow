import type { DeckStyle, Difficulty } from '../types';

interface SettingsPanelProps {
  deckStyle: DeckStyle;
  difficulty: Difficulty;
  reducedMotion: boolean;
  onDeckStyleChange: (value: DeckStyle) => void;
  onDifficultyChange: (value: Difficulty) => void;
  onReducedMotionChange: (value: boolean) => void;
}

export function SettingsPanel({
  deckStyle,
  difficulty,
  reducedMotion,
  onDeckStyleChange,
  onDifficultyChange,
  onReducedMotionChange,
}: SettingsPanelProps) {
  return (
    <section className="side-card">
      <p className="eyebrow">Preferences</p>
      <h2>Table settings</h2>

      <div className="setting-group">
        <label htmlFor="deck-style">Deck style</label>
        <select
          id="deck-style"
          value={deckStyle}
          onChange={(event) => onDeckStyleChange(event.target.value as DeckStyle)}
        >
          <option value="four_color">Four-color deck</option>
          <option value="standard">Standard red/black</option>
        </select>
      </div>

      <div className="setting-group">
        <label htmlFor="difficulty">Bot difficulty</label>
        <select
          id="difficulty"
          value={difficulty}
          onChange={(event) => onDifficultyChange(event.target.value as Difficulty)}
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={reducedMotion}
          onChange={(event) => onReducedMotionChange(event.target.checked)}
        />
        <span>Reduced motion</span>
      </label>
    </section>
  );
}
