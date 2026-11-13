# BentleyBooVR Stationary NPC — First Design Pass

## Goal

Add a friendly, custom-looking BentleyBooVR character at the Animal Company spawn area. The character should remain stationary. The player continues running Animal Company directly on a standalone Meta Quest; the Windows PC hosts the companion voice service.

## First visual prototype

- A simple, original, friendly animal-companion mascot.
- A clearly visible name label: **BentleyBooVR**.
- A relaxed idle pose; no roaming, chasing, or player movement.
- A small interaction cue so players know the character is the voice companion.
- Keep the first version visually simple so it can be tested before adding more features.

## Planned interaction

1. The player approaches the character and uses the game's supported interaction method.
2. The companion opens or activates the voice interaction.
3. BentleyBooVR listens and repeats the request.
4. It asks for a clear yes/no confirmation.
5. The voice service reports the answer. It does not perform a game action unless a separately authorized, supported game integration exists.

## Architecture

- **Windows PC:** hosts the existing FastAPI companion service and AI voice.
- **Standalone Quest:** runs Animal Company normally.
- **Game-side NPC:** would need to be implemented through an official developer-supported integration or explicitly authorized Quest-compatible modding API.
- **Connection:** only a documented, permissioned interface should connect the in-game interaction to the PC service.

## Current limitations

This is a design specification, not an installed or working in-game NPC. The current repository contains the voice/confirmation service and a fail-closed game bridge, but it does not add objects to Animal Company.

Before writing game-side code, verify that the game developer permits the relevant modding method and that it supports the standalone Quest build. A PC-hosted service alone cannot insert a character into the Quest game. Do not use private game endpoints, account/session credentials, traffic interception, or anti-cheat bypasses.

## First milestone

Build and test a harmless visual mascot concept independently. Only after an authorized Quest-compatible integration is confirmed should it be connected to the Animal Company spawn scene.
