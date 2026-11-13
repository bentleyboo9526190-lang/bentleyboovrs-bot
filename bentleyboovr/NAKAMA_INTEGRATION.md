# Optional Nakama backend for BentleyBooVR

## What this library is

[`github.com/ascii8/nakama-go`](https://github.com/ascii8/nakama-go) is a Go client for a Nakama game server. It supports Nakama's web API and realtime WebSocket features, and can be used by Go and WebAssembly clients.

It is a **client SDK**, not a Nakama server, Unity/Quest mod loader, Animal Company plugin, or tool for joining an unrelated game's servers.

## What it could do for this project

If BentleyBooVR later runs its own Nakama server, a small Go service using this SDK could provide project-owned features such as:
- BentleyBooVR companion chat rooms.
- Presence for people using the companion app.
- Realtime messages between the companion UI and the PC-hosted bot.
- Project-owned sessions or matchmaking for a separate BentleyBooVR experience.

The existing companion is a Python/FastAPI app. This Go SDK cannot be installed through Python's `requirements.txt`; it would need a separate Go component, plus a Nakama server to connect to. Neither is configured by this design note.

## Animal Company boundary

Nakama only connects to a Nakama server that is configured for it. Adding this SDK does not make BentleyBooVR an Animal Company player, does not provide access to Animal Company rooms, and does not create an in-game NPC. Those would require an official integration or explicit authorization from the game developer.

Do not point this client at private game services, use game-account credentials or session tokens, imitate the game's private protocol, or attempt to bypass access controls.

## Suggested development order

1. Keep the current Python companion working independently.
2. If a separate BentleyBooVR companion backend is wanted, set up a Nakama server owned by this project.
3. Add a small Go service using `ascii8/nakama-go` to connect to that project-owned server.
4. Connect the companion UI to that service using documented project APIs.
5. Keep all game-facing features disabled unless an authorized Animal Company integration becomes available.

No Nakama connection or Animal Company connection is active yet.
