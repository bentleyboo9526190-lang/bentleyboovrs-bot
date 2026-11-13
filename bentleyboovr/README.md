# BentleyBooVR Bot

A local companion service for the BentleyBooVR Animal Company project.

## Current prototype

This first version provides:
- A health endpoint.
- A request endpoint that repeats the user's requested action and asks for confirmation.
- A confirmation endpoint that records yes/no decisions.

**Important:** This prototype does not join Animal Company, control a player, or spawn game items. Those capabilities require an authorized, supported game integration. Do not add account passwords, session tokens, or private credentials to this repository.

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

6. Open http://127.0.0.1:8000/docs to try the prototype.

The service listens only on the PC itself by default. Keep it that way for the first test; don't expose it to the public internet.
