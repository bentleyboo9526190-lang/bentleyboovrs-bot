# Optional Nakama backend for BentleyBooVR

## What this library is

[`github.com/ascii8/nakama-go`](https://github.com/ascii8/nakama-go) is a Go client for a Nakama game server. It supports Nakama's web API and realtime WebSocket features, and can be used by Go and WebAssembly clients.

It is a **client SDK**, not a Nakama server, Unity/Quest mod loader, Animal Company plugin, or tool for joining an unrelated game's servers.

## What is now in the repository

The first local backend scaffold is committed:

- `nakama/docker-compose.yml` starts a project-owned Nakama server and PostgreSQL database.
- `nakama-bridge/` is a Go service using `ascii8/nakama-go`.
- The Go bridge checks the local Nakama health endpoint.
- The Python companion exposes `GET /nakama/status` to report whether the bridge can reach Nakama.

This is a connectivity foundation only. It does not yet create user accounts, chat rooms, presence, or matchmaking. The server and bridge must still be started on the user's Windows PC before a live connection can be verified.

## Safe local setup

See [the main README](README.md) and [the Go bridge README](nakama-bridge/README.md) for the Windows setup steps.

The Docker Compose ports are bound to localhost, and PostgreSQL is not published outside the Docker network. Keep this as a local development environment; do not expose it publicly or put credentials/tokens in source control.

## Animal Company boundary

This Nakama instance belongs to BentleyBooVR. It does not connect to Animal Company's backend, does not make BentleyBooVR an Animal Company player, does not provide access to Animal Company rooms, and does not create an in-game NPC. Those would require an official integration or explicit authorization from the game developer.

Do not point this client at private game services, use game-account credentials or session tokens, imitate the game's private protocol, or attempt to bypass access controls.

## Next development steps

1. Run the local Nakama server and Go bridge, then verify `/nakama/status`.
2. Design a separate BentleyBooVR identity and account flow.
3. Add project-owned chat/presence features using Nakama's documented APIs.
4. Keep all game-facing features disabled unless an authorized Animal Company integration becomes available.
