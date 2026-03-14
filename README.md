# Premium Poker

A modern, minimal Texas Hold'em web app built for local-first play, mocked multiplayer, and future Firebase deployment.

## Current implementation status

This repository now contains the initial production-oriented scaffold:

- `apps/web`: React + Vite frontend with a premium poker UI shell
- `apps/game-api`: FastAPI backend with mock auth, room APIs, and a deterministic poker engine skeleton
- `packages/contracts`: shared API examples and generated-contract placeholder
- `packages/design-tokens`: shared visual tokens
- `docs`: architecture and migration notes

The current version is an implementation foundation, not a finished game. It is structured so the poker engine, bot engine, and UI can be extended without rewrites.

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

- Local profile creation UI shell
- Room create/join UI shell
- Premium table layout shell with seats, board, action bar, and settings panel
- Backend health check
- Mock session API
- Room create/join/list APIs
- WebSocket room stream scaffold
- Deterministic card/deck helpers and hand state models

## What to build next

1. Complete the reducer-driven poker engine
2. Add bot decision policies and opponent memory
3. Wire the frontend to the WebSocket room state stream
4. Persist profiles, preferences, and hand history
5. Add Firebase-backed auth and room metadata

## Offline mode

Offline mode means the app runs entirely on one machine with a local frontend and local Python backend. No cloud services are required for development or play testing.

## Firebase migration

The app is designed so Firebase is added at the auth, hosting, and persistence edges. The Python service remains authoritative for rules and hand resolution.
