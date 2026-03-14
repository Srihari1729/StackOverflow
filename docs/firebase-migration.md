# Firebase Migration Notes

## Keep stable from day 1

- Session and profile contracts
- Room creation and join contracts
- WebSocket or realtime event payload structure
- Game engine command/event boundaries

## Recommended production shape

- Firebase Hosting for the SPA
- Firebase Auth for user identity
- Cloud Run for the FastAPI service
- Firestore for profiles, room metadata, and hand summaries
- Optional Realtime Database for presence only

## Avoid

- Moving authoritative hand resolution into frontend clients
- Treating Firestore security rules as game-rule enforcement
- Encoding poker logic directly into Firebase document triggers
