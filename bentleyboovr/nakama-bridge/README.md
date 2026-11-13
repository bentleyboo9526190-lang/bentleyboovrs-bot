# BentleyBooVR Nakama bridge

This small Go service uses [ascii8/nakama-go](https://github.com/ascii8/nakama-go) to check the health of the Nakama server owned by this project.

## Start the local Nakama server

From the `bentleyboovr/nakama` directory:

```powershell
docker compose up -d
docker compose ps
```

The server's HTTP API is bound to localhost on port 7350 and the developer console to localhost on port 7351. PostgreSQL is only reachable inside the Docker network. These defaults are for local development, not public hosting.

## Start the Go bridge

Install Go 1.22 or newer, then from `bentleyboovr/nakama-bridge`:

```powershell
go mod tidy
go run .
```

The bridge listens only on `127.0.0.1:8081`.

- `GET http://127.0.0.1:8081/health` checks that the bridge process is running.
- `GET http://127.0.0.1:8081/status` checks the actual Nakama server using the Go SDK.

The Go SDK defaults to `http://127.0.0.1:7350`, matching the local Compose setup. Do not expose either service to the public internet or put credentials/tokens in source control.

This first bridge only verifies connectivity. It does not create accounts, chat rooms, matchmaking, or any Animal Company connection. Those can be added later for BentleyBooVR's own backend with appropriate account and privacy design.
