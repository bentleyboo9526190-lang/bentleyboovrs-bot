# BentleyBooVR Bot

A local companion service for the BentleyBooVR Animal Company project.

## Current prototype

This first version provides:
- A browser voice page at `/voice` with microphone speech recognition where the browser supports it.
- Spoken responses using the browser's built-in speech synthesis.
- A request endpoint that repeats the user's requested action and asks for confirmation.
- Yes/no confirmation buttons that record the decision.

**Important:** The voice page uses your browser's speech features; it is not yet a custom deep AI voice. This prototype does not join Animal Company, control a player, or spawn game items. Those capabilities require an authorized, supported game integration. Do not add account passwords, session tokens, or private credentials to this repository.

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

5. Start the local service:

   ```powershell
   py -m uvicorn companion:app --host 127.0.0.1 --port 8000
   ```

6. Open http://127.0.0.1:8000/voice to try the voice page. If microphone recognition is unavailable in your browser, type a request instead.
7. Open http://127.0.0.1:8000/docs to inspect the API.

The service listens only on the PC itself by default. Keep it that way for the first test; don't expose it to the public internet.
