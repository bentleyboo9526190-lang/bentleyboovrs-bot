# BentleyBooVR Bot

A local companion service for the BentleyBooVR Animal Company project.

## Current prototype

This first version provides:
- A browser voice page at `/voice` with microphone speech recognition where the browser supports it.
- Optional AI-generated spoken replies through a server-side speech endpoint, using a lower-register voice style.
- Device speech fallback with a voice picker and adjustable pitch/speed if AI speech is not configured.
- BentleyBooVR's companion-style response wording.
- A request endpoint that repeats the user's requested action and asks for confirmation.
- Yes/no confirmation buttons that record the decision.

**Important:** The AI speech endpoint uses OpenAI's Speech API and the `gpt-4o-mini-tts` model with the `onyx` voice and a lower-register delivery instruction. OpenAI currently lists this model as deprecated with a scheduled shutdown on January 6, 2027; this is a temporary integration that will need migration to the Realtime API before then. See the [official text-to-speech guide](https://developers.openai.com/api/docs/guides/text-to-speech). The audio is AI-generated and the page labels it as such. Never commit API keys to this public repository. This prototype does not join Animal Company, control a player, or spawn game items. Those capabilities require an authorized, supported game integration. Do not add account passwords, session tokens, or private credentials to this repository.

## Run on Windows

1. Install Python 3.11 or newer.
2. Open PowerShell in this folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. (Optional) Configure the AI voice key in this PowerShell window. Keep the key private; do not paste it into GitHub, chat, or source code. If you do not have an API account/key, ask a parent or guardian to help with account and billing decisions. The browser voice fallback still works without this setting.

   ```powershell
   $env:OPENAI_API_KEY = "paste-your-private-key-here"
   ```

6. Start the local service:

   ```powershell
   py -m uvicorn companion:app --host 127.0.0.1 --port 8000
   ```

7. Open http://127.0.0.1:8000/voice to try the voice page. If AI speech is not configured, it falls back to the device voice. If microphone recognition is unavailable in your browser, type a request instead.
8. Open http://127.0.0.1:8000/docs to inspect the API.

The service listens only on the PC itself by default. Keep it that way for the first test; don't expose it to the public internet.


## Animal Company game layer

A safe integration boundary is now included:

- `GET /game/status` reports which game capabilities are actually available.
- `POST /game/command` fails closed with HTTP 501 while no authorized game adapter exists. It does not send anything to Animal Company.

At present, joining room `BENTLEYBOOVR`, controlling an avatar, reading live game state, and spawning items are **not implemented**. This requires an official integration or a modding API whose use is explicitly authorized by the game developer. The project will not use private backend endpoints, authentication/session tokens, traffic interception, or anti-cheat bypasses as a substitute.

## Optional project-owned Nakama backend

A separate local Nakama server and Go SDK bridge are now scaffolded:

- `nakama/docker-compose.yml` starts Nakama plus its PostgreSQL database.
- `nakama-bridge/` is a Go service using `github.com/ascii8/nakama-go`.
- The Go bridge checks the Nakama server at `http://127.0.0.1:7350`.
- `GET /nakama/status` on the Python companion reports whether that bridge can reach Nakama.

### Start it on Windows

1. Install Docker Desktop and Go 1.22 or newer.
2. In PowerShell, start the database and Nakama server:

   ```powershell
   cd bentleyboovr/nakama
   docker compose up -d
   ```

3. In a second PowerShell window, start the Go bridge:

   ```powershell
   cd bentleyboovr/nakama-bridge
   go mod tidy
   go run .
   ```

4. Start the Python companion as described above.
5. Open `http://127.0.0.1:8000/nakama/status` to check the connection.

The Nakama API and console ports are bound to localhost; PostgreSQL is internal to Docker. Keep this setup local and do not expose it to the public internet. The initial bridge only checks connectivity; it does not yet implement accounts, chat, presence, or matchmaking. This backend belongs to BentleyBooVR and is not connected to Animal Company.

See [the bridge setup notes](nakama-bridge/README.md) for details.
