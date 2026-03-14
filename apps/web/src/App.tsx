import { useEffect, useState } from 'react';
import { createMockSession, createRoom, fetchHealth, getRoom, joinRoom, sendAction, startHand } from './api';
import { CommunityBoard } from './components/CommunityBoard';
import { Seat } from './components/Seat';
import { SettingsPanel } from './components/SettingsPanel';
import type { ActionType, DeckStyle, Difficulty, RoomConfigInput, RoomState, RoomViewResponse } from './types';

const SESSION_ID_KEY = 'premium-poker-session-id';
const DISPLAY_NAME_KEY = 'premium-poker-display-name';

const defaultConfig: RoomConfigInput = {
  maxSeats: 6,
  botCount: 4,
  smallBlind: 10,
  bigBlind: 20,
  startingStack: 2000,
  difficulty: 'medium',
};

function App() {
  const [deckStyle, setDeckStyle] = useState<DeckStyle>('four_color');
  const [reducedMotion, setReducedMotion] = useState(false);
  const [displayName, setDisplayName] = useState(localStorage.getItem(DISPLAY_NAME_KEY) ?? 'Srihari');
  const [sessionId, setSessionId] = useState(localStorage.getItem(SESSION_ID_KEY) ?? '');
  const [apiStatus, setApiStatus] = useState('Checking local API...');
  const [statusMessage, setStatusMessage] = useState('Create or join a room to begin.');
  const [config, setConfig] = useState<RoomConfigInput>(defaultConfig);
  const [joinCode, setJoinCode] = useState('');
  const [currentRoomCode, setCurrentRoomCode] = useState('');
  const [roomView, setRoomView] = useState<RoomViewResponse | null>(null);
  const [raiseAmount, setRaiseAmount] = useState(80);
  const [isBusy, setIsBusy] = useState(false);

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
          setApiStatus('Backend offline. Start FastAPI on port 8000.');
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!currentRoomCode || !sessionId) {
      return undefined;
    }
    let cancelled = false;
    const poll = async () => {
      try {
        const latest = await getRoom(currentRoomCode, sessionId);
        if (!cancelled) {
          setRoomView(latest);
          if (latest.room.hand_state?.min_raise_to) {
            setRaiseAmount(latest.room.hand_state.min_raise_to);
          }
        }
      } catch (error) {
        if (!cancelled) {
          setStatusMessage(error instanceof Error ? error.message : 'Failed to refresh room');
        }
      }
    };
    void poll();
    const interval = window.setInterval(poll, 700);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [currentRoomCode, sessionId]);

  async function ensureSession(): Promise<string> {
    if (sessionId) {
      return sessionId;
    }
    const session = await createMockSession(displayName.trim());
    localStorage.setItem(SESSION_ID_KEY, session.session_id);
    localStorage.setItem(DISPLAY_NAME_KEY, session.display_name);
    setSessionId(session.session_id);
    setDisplayName(session.display_name);
    return session.session_id;
  }

  async function refreshRoom(roomCode: string, activeSessionId: string) {
    const next = await getRoom(roomCode, activeSessionId);
    setRoomView(next);
    setCurrentRoomCode(roomCode);
    if (next.room.hand_state?.min_raise_to) {
      setRaiseAmount(next.room.hand_state.min_raise_to);
    }
  }

  async function handleCreateRoom() {
    setIsBusy(true);
    try {
      const activeSessionId = await ensureSession();
      const room = await createRoom(activeSessionId, config);
      if (config.botCount > 0) {
        await startHand(room.room_code, activeSessionId);
        await refreshRoom(room.room_code, activeSessionId);
        setStatusMessage(`Created room ${room.room_code}. Your first hand is live.`);
      } else {
        await refreshRoom(room.room_code, activeSessionId);
        setStatusMessage(`Created room ${room.room_code}. Add players or start when ready.`);
      }
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Failed to create room');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleJoinRoom() {
    setIsBusy(true);
    try {
      const activeSessionId = await ensureSession();
      const room = await joinRoom(activeSessionId, joinCode);
      await refreshRoom(room.room_code, activeSessionId);
      setStatusMessage(`Joined room ${room.room_code}`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Failed to join room');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleStartHand() {
    if (!currentRoomCode) {
      return;
    }
    setIsBusy(true);
    try {
      const activeSessionId = await ensureSession();
      await startHand(currentRoomCode, activeSessionId);
      await refreshRoom(currentRoomCode, activeSessionId);
      setStatusMessage('Hand started');
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Failed to start hand');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAction(action: ActionType) {
    if (!currentRoomCode) {
      return;
    }
    setIsBusy(true);
    try {
      const activeSessionId = await ensureSession();
      const actionAmount = action === 'raise' ? minRaiseAmount : action === 'all_in' ? maxRaiseTo : 0;
      await sendAction(currentRoomCode, activeSessionId, action, actionAmount);
      await refreshRoom(currentRoomCode, activeSessionId);
      setStatusMessage(`Submitted ${action}`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Action failed');
    } finally {
      setIsBusy(false);
    }
  }

  const room: RoomState | null = roomView?.room ?? null;
  const legalActions = roomView?.legal_actions ?? [];
  const isHost = !!room && room.host_session_id === sessionId;
  const viewerName = displayName || 'Player';
  const actingSeat = room?.hand_state?.acting_seat != null ? room.seats[room.hand_state.acting_seat] : null;
  const viewerSeat = room?.seats.find((seat) => seat.occupant_id === sessionId) ?? null;
  const isViewerTurn = !!actingSeat && actingSeat.occupant_id === sessionId;
  const toCall = room?.hand_state && viewerSeat ? Math.max(0, room.hand_state.current_bet - viewerSeat.current_bet) : 0;
  const minRaiseTo = room?.hand_state?.min_raise_to ?? 0;
  const maxRaiseTo = viewerSeat ? viewerSeat.current_bet + viewerSeat.stack : 0;
  const minRaiseAmount = minRaiseTo > 0 ? Math.min(Math.max(minRaiseTo, raiseAmount), maxRaiseTo || minRaiseTo) : raiseAmount;

  useEffect(() => {
    if (!room) {
      return;
    }
    if (room.status === 'hand_over' && room.hand_state?.winner_text) {
      setStatusMessage(room.hand_state.winner_text);
      return;
    }
    if (actingSeat?.occupant_id === sessionId) {
      setStatusMessage(toCall > 0 ? `Your turn. Call ${toCall}, fold, or raise.` : 'Your turn. Check or bet.');
      return;
    }
    if (actingSeat?.occupant_name) {
      setStatusMessage(`${actingSeat.occupant_name} is acting.`);
      return;
    }
    if (room.status === 'lobby') {
      setStatusMessage('Room ready. Start a hand when you want to play.');
    }
  }, [room, actingSeat, sessionId, toCall]);

  function applyRaisePreset(target: number) {
    if (!room || !viewerSeat) {
      return;
    }
    const clamped = Math.max(minRaiseTo, Math.min(target, viewerSeat.current_bet + viewerSeat.stack));
    setRaiseAmount(clamped);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Premium Poker</p>
          <h1>Calm poker. Real backend state. Bots with actual turns and hand flow.</h1>
        </div>

        <div className="profile-chip">
          <div className="seat-avatar" style={{ background: '#3f7cff' }}>
            {viewerName.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <strong>{viewerName}</strong>
            <p className="muted">{sessionId ? 'Local session active' : 'No local session yet'}</p>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="left-rail">
          <article className="side-card">
            <p className="eyebrow">Identity</p>
            <h2>Mock local player</h2>
            <p className="muted status-copy">{apiStatus}</p>
            <div className="setting-group">
              <label htmlFor="display-name">Display name</label>
              <input
                id="display-name"
                value={displayName}
                maxLength={24}
                onChange={(event) => setDisplayName(event.target.value)}
              />
            </div>
          </article>

          <article className="side-card">
            <p className="eyebrow">Room setup</p>
            <h2>Create room</h2>
            <div className="inline-grid">
              <div className="setting-group">
                <label htmlFor="max-seats">Seats</label>
                <select
                  id="max-seats"
                  value={config.maxSeats}
                  onChange={(event) =>
                    setConfig((current) => {
                      const maxSeats = Number(event.target.value);
                      return {
                        ...current,
                        maxSeats,
                        botCount: Math.min(current.botCount, maxSeats - 1),
                      };
                    })
                  }
                >
                  {[2, 3, 4, 5, 6].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-group">
                <label htmlFor="bot-count">Bots</label>
                <select
                  id="bot-count"
                  value={config.botCount}
                  onChange={(event) => setConfig((current) => ({ ...current, botCount: Number(event.target.value) }))}
                >
                  {Array.from({ length: config.maxSeats }, (_, index) => index).map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="inline-grid">
              <div className="setting-group">
                <label htmlFor="small-blind">Small blind</label>
                <input
                  id="small-blind"
                  type="number"
                  value={config.smallBlind}
                  min={1}
                  onChange={(event) => setConfig((current) => ({ ...current, smallBlind: Number(event.target.value) }))}
                />
              </div>

              <div className="setting-group">
                <label htmlFor="big-blind">Big blind</label>
                <input
                  id="big-blind"
                  type="number"
                  value={config.bigBlind}
                  min={2}
                  onChange={(event) => setConfig((current) => ({ ...current, bigBlind: Number(event.target.value) }))}
                />
              </div>
            </div>

            <div className="inline-grid">
              <div className="setting-group">
                <label htmlFor="starting-stack">Starting stack</label>
                <input
                  id="starting-stack"
                  type="number"
                  value={config.startingStack}
                  min={100}
                  step={100}
                  onChange={(event) => setConfig((current) => ({ ...current, startingStack: Number(event.target.value) }))}
                />
              </div>

              <div className="setting-group">
                <label htmlFor="difficulty">Bot difficulty</label>
                <select
                  id="difficulty"
                  value={config.difficulty}
                  onChange={(event) => setConfig((current) => ({ ...current, difficulty: event.target.value as Difficulty }))}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <div className="button-row">
              <button className="primary-button" onClick={handleCreateRoom} disabled={isBusy}>
                {isBusy ? 'Working...' : 'Create room'}
              </button>
            </div>
          </article>

          <article className="side-card">
            <p className="eyebrow">Join room</p>
            <h2>Use a code</h2>
            <div className="setting-group">
              <label htmlFor="join-code">Room code</label>
              <input
                id="join-code"
                value={joinCode}
                maxLength={6}
                onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
              />
            </div>
            <div className="button-row">
              <button className="secondary-button" onClick={handleJoinRoom} disabled={isBusy || joinCode.length < 6}>
                Join
              </button>
            </div>
          </article>

          <SettingsPanel
            deckStyle={deckStyle}
            reducedMotion={reducedMotion}
            onDeckStyleChange={setDeckStyle}
            onReducedMotionChange={setReducedMotion}
          />
        </section>

        <section className="table-stage">
          <CommunityBoard handState={room?.hand_state ?? null} roomStatus={room?.status ?? 'lobby'} />

          <div className="table-meta">
            <div className="meta-chip">
              <span className="stat-label">Room</span>
              <strong>{room?.room_code ?? '------'}</strong>
            </div>
            <div className="meta-chip">
              <span className="stat-label">Status</span>
              <strong>{room?.status ?? 'idle'}</strong>
            </div>
            <div className="meta-chip wide-chip">
              <span className="stat-label">Update</span>
              <strong>{statusMessage}</strong>
            </div>
          </div>

          <div className="seat-grid">
            {(room?.seats ?? []).map((seat) => (
              <Seat
                key={`${seat.seat_index}-${seat.occupant_id ?? 'open'}`}
                seat={seat}
                isViewer={seat.occupant_id === sessionId}
                isActing={room?.hand_state?.acting_seat === seat.seat_index}
              />
            ))}
          </div>

          <footer className="action-bar action-panel">
            <div className="action-summary">
              <p className="eyebrow">Action</p>
              <h2>
                {room?.hand_state?.completed
                  ? room.hand_state.winner_text || 'Hand complete'
                  : isViewerTurn
                    ? 'Your move'
                    : actingSeat?.occupant_name
                      ? `${actingSeat.occupant_name} is acting`
                      : 'Waiting for hand'}
              </h2>
              <p className="muted">
                {room?.hand_state
                  ? `Street: ${room.hand_state.street} · Pot ${room.hand_state.pot_total}`
                  : 'Create a room and play locally with bots.'}
              </p>
            </div>

            <div className="action-strip">
              {(room?.status === 'lobby' || room?.status === 'hand_over') && isHost ? (
                <button className="primary-button large-button" onClick={handleStartHand} disabled={isBusy}>
                  {room?.status === 'hand_over' ? 'Deal next hand' : 'Deal first hand'}
                </button>
              ) : null}

              {room?.hand_state && isViewerTurn ? (
                <>
                  <div className="action-primary-group">
                    {legalActions.includes('fold') ? (
                      <button className="danger-button" onClick={() => handleAction('fold')} disabled={isBusy}>
                        Fold
                      </button>
                    ) : null}
                    {legalActions.includes('check') ? (
                      <button className="secondary-button large-button" onClick={() => handleAction('check')} disabled={isBusy}>
                        Check
                      </button>
                    ) : null}
                    {legalActions.includes('call') ? (
                      <button className="primary-button large-button" onClick={() => handleAction('call')} disabled={isBusy}>
                        Call ${toCall}
                      </button>
                    ) : null}
                  </div>

                  {(legalActions.includes('raise') || legalActions.includes('all_in')) && viewerSeat ? (
                    <div className="raise-panel">
                      <div className="raise-presets">
                        <button
                          className="chip-button"
                          onClick={() => applyRaisePreset(minRaiseTo)}
                          disabled={isBusy}
                        >
                          Min {minRaiseTo}
                        </button>
                        <button
                          className="chip-button"
                          onClick={() => applyRaisePreset((room.hand_state?.pot_total ?? 0) + (room.hand_state?.current_bet ?? 0))}
                          disabled={isBusy}
                        >
                          Pot
                        </button>
                        <button
                          className="chip-button"
                          onClick={() => applyRaisePreset(maxRaiseTo)}
                          disabled={isBusy}
                        >
                          All-in
                        </button>
                      </div>

                      <div className="raise-block">
                        <label className="raise-label" htmlFor="raise-amount">
                          Raise to
                        </label>
                        <input
                          id="raise-amount"
                          type="number"
                          value={minRaiseAmount}
                          min={minRaiseTo || room.config.big_blind}
                          max={maxRaiseTo || undefined}
                          onChange={(event) => setRaiseAmount(Number(event.target.value))}
                        />
                        {legalActions.includes('raise') ? (
                          <button className="primary-button" onClick={() => handleAction('raise')} disabled={isBusy}>
                            Raise to ${minRaiseAmount}
                          </button>
                        ) : null}
                        {legalActions.includes('all_in') ? (
                          <button className="secondary-button" onClick={() => handleAction('all_in')} disabled={isBusy}>
                            Shove ${maxRaiseTo}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          </footer>

          {room?.hand_state?.action_log?.length ? (
            <section className="side-card history-panel">
              <p className="eyebrow">Hand history</p>
              <h2>Latest actions</h2>
              <div className="history-list">
                {room.hand_state.action_log.slice(-8).reverse().map((entry) => (
                  <div key={entry.order} className="history-item">
                    <strong>{entry.actor_name}</strong>
                    <span>
                      {entry.action}
                      {entry.target_bet ? ` to ${entry.target_bet}` : entry.amount ? ` ${entry.amount}` : ''}
                      {entry.note ? ` · ${entry.note}` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}
        </section>
      </main>
    </div>
  );
}

export default App;
