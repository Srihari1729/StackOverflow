# Architecture

## Principles

- Backend owns game legality, hidden information, and future bot logic.
- Frontend owns presentation, local preferences, and user flow polish.
- Local-first mode avoids cloud dependencies.
- Firebase is an adapter concern, not a game-engine concern.

## Runtime shape

```text
React frontend -> REST/WebSocket -> FastAPI application
                                 -> poker domain
                                 -> bot domain
                                 -> room service
```

## Key boundaries

- `app.api`: HTTP and WebSocket transport only
- `app.services`: application orchestration
- `app.domain.poker`: pure game state and rule helpers
- `app.domain.bots`: decision policies and opponent memory
- `app.infrastructure`: persistence/auth provider implementations
