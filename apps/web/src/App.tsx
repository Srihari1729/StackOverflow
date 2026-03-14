import { useEffect, useState } from 'react';
import { createMockSession, createRoom, fetchHealth } from './api';
import { CommunityBoard } from './components/CommunityBoard';
import { Seat } from './components/Seat';
import { SettingsPanel } from './components/SettingsPanel';
import { createMockSeats, defaultRoomConfig, hostProfile } from './data';
import type { DeckStyle, Difficulty } from './types';

function App() {
  const [deckStyle, setDeckStyle] = useState<DeckStyle>('four_color');
  const [difficulty, setDifficulty] = useState<Difficulty>(defaultRoomConfig.difficulty);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [roomCode, setRoomCode] = useState(defaultRoomConfig.roomCode);
  const [apiStatus, setApiStatus] = useState('Checking local API...');
  const [createStatus, setCreateStatus] = useState('Backend room creation ready');
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const seats = createMockSeats(hostProfile).map((seat) =>
    seat.isBot && difficulty === 'hard' && seat.status === 'ready'
      ? { ...seat, status: 'acting' as const }
      : seat,
  );

  useEffect(() => {
    document.documentElement.dataset.deckStyle = deckStyle;
    document.documentElement.dataset.motion = reducedMotion ? 'reduced' : 'full';
  }, [deckStyle, reducedMotion]);

  useEffect(() => {
    let isMounted = true;

    fetchHealth()
      .then(() => {
        if (isMounted) {
          setApiStatus('Local API online');
        }
      })
      .catch(() => {
        if (isMounted) {
          setApiStatus('Backend offline. Start FastAPI to enable room creation.');
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleCreateRoom() {
    setIsCreatingRoom(true);
    setCreateStatus('Creating session and room...');

    try {
      const session =
        sessionStorage.getItem('premium-poker-session-id') ??
        (await createMockSession(hostProfile.displayName)).session_id;

      sessionStorage.setItem('premium-poker-session-id', session);
      const room = await createRoom(session, difficulty);
      setRoomCode(room.room_code);
      setCreateStatus(`Created room ${room.room_code}`);
    } catch (error) {
      setCreateStatus(
        error instanceof Error ? error.message : 'Could not create room. Check the backend.',
      );
    } finally {
      setIsCreatingRoom(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Premium Poker</p>
          <h1>Offline-first Texas Hold&apos;em with a calm, modern table.</h1>
        </div>

        <div className="profile-chip">
          <div className="seat-avatar" style={{ background: hostProfile.avatarTone }}>
            {hostProfile.avatarSeed}
          </div>
          <div>
            <strong>{hostProfile.displayName}</strong>
            <p className="muted">Mock local session active</p>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="left-rail">
          <article className="side-card">
            <p className="eyebrow">Room</p>
            <h2>Create or join</h2>
            <p className="muted status-copy">{apiStatus}</p>
            <div className="stat-grid">
              <div>
                <span className="stat-label">Code</span>
                <strong>{roomCode}</strong>
              </div>
              <div>
                <span className="stat-label">Blinds</span>
                <strong>
                  {defaultRoomConfig.smallBlind}/{defaultRoomConfig.bigBlind}
                </strong>
              </div>
              <div>
                <span className="stat-label">Seats</span>
                <strong>{defaultRoomConfig.seats}</strong>
              </div>
              <div>
                <span className="stat-label">Bots</span>
                <strong>{defaultRoomConfig.bots}</strong>
              </div>
            </div>

            <div className="button-row">
              <button className="primary-button" onClick={handleCreateRoom} disabled={isCreatingRoom}>
                {isCreatingRoom ? 'Creating...' : 'Create room'}
              </button>
              <button className="secondary-button">Join code</button>
            </div>
            <p className="muted status-copy">{createStatus}</p>
          </article>

          <SettingsPanel
            deckStyle={deckStyle}
            difficulty={difficulty}
            reducedMotion={reducedMotion}
            onDeckStyleChange={setDeckStyle}
            onDifficultyChange={setDifficulty}
            onReducedMotionChange={setReducedMotion}
          />
        </section>

        <section className="table-stage">
          <CommunityBoard />

          <div className="seat-grid">
            {seats.map((seat) => (
              <Seat key={`${seat.seatIndex}-${seat.name}`} seat={seat} />
            ))}
          </div>

          <footer className="action-bar">
            <div>
              <p className="eyebrow">Action</p>
              <h2>Your turn</h2>
            </div>

            <div className="button-row">
              <button className="secondary-button">Fold</button>
              <button className="secondary-button">Call 120</button>
              <button className="primary-button">Raise to 280</button>
            </div>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
