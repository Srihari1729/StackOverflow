import type { DeckStyle } from '../types';

interface SettingsPanelProps {
  deckStyle: DeckStyle;
  reducedMotion: boolean;
  onDeckStyleChange: (value: DeckStyle) => void;
  onReducedMotionChange: (value: boolean) => void;
}

export function SettingsPanel({
  deckStyle,
  reducedMotion,
  onDeckStyleChange,
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
