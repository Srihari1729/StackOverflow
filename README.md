# Premium Poker

A modern, minimal Texas Hold'em web app built for local-first play, mocked multiplayer, and future Firebase deployment.

## Current implementation status

This repository now contains a working local-first gameplay slice:

- `apps/web`: React + Vite frontend with live room creation, join flow, table state polling, and playable action controls
- `apps/game-api`: FastAPI backend with mock auth, room APIs, a deterministic poker engine, and bot automation
- `packages/contracts`: shared API examples and generated-contract placeholder
- `packages/design-tokens`: shared visual tokens
- `docs`: architecture and migration notes

The current version supports a real local room lifecycle and playable single-table Hold'em hands with bots. It is still offline-first and intentionally local, but it is no longer just a UI scaffold.

## Stack

- Frontend: React, TypeScript, Vite, React Router, Zustand, Tailwind-free custom token CSS
- Backend: Python, FastAPI, Pydantic
- Local persistence path: browser storage for preferences, in-memory rooms for runtime, backend-ready persistence seams
- Future path: Firebase Auth + Hosting + Cloud Run + Firestore

## Repository layout

```text
apps/
  web/
  game-api/
packages/
  contracts/
  design-tokens/
  ui/
docs/
tests/
```

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.9+
- `python3 -m venv`

## Install

Frontend dependencies:

```bash
npm install
```

Backend environment:

```bash
cd apps/game-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run locally

Frontend:

```bash
npm run dev:web
```

Backend:

```bash
cd apps/game-api
source .venv/bin/activate
uvicorn app.main:app --reload
```

Frontend runs on `http://localhost:5173` by default. Backend runs on `http://127.0.0.1:8000`.

## What exists today

- Local mock session bootstrap
- Room create/join flow with configurable seats, bots, blinds, and starting stack
- Premium table UI driven by live backend room state
- Start hand / next hand flow
- Legal-action aware controls for fold, check, call, raise, and all-in
- Deterministic shuffle/deal, blind posting, turn order, street advancement, showdown, and pot settlement
- Difficulty-based bots with lightweight opponent-memory updates
- Hidden bot hole cards in player-facing room views until showdown
- Hand history panel and winner summaries
- Backend health check
- Mock session API
- Room create/join/get/start/action APIs
- WebSocket room stream scaffold
- Deterministic card/deck helpers and hand evaluator

## What to build next

1. Replace polling with WebSocket-driven room updates
2. Expand opponent modeling and bot strategy depth
3. Add persistence for local profiles, room history, and preferences
4. Improve reconnect handling and multi-human tab flows
5. Add Firebase-backed auth and room metadata

## Offline mode

Offline mode means the app runs entirely on one machine with a local frontend and local Python backend. No cloud services are required for development or play testing.

## Firebase migration

The app is designed so Firebase is added at the auth, hosting, and persistence edges. The Python service remains authoritative for rules and hand resolution.
