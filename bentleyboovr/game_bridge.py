"""Safe Animal Company integration boundary.

This module deliberately does not connect to private game services, inject code,
or manipulate game traffic. A real adapter can only be added against an
officially supported integration or an explicitly authorized modding API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Animal Company game bridge"])


class GameCommand(BaseModel):
    action: str = Field(min_length=1, max_length=120)


@router.get("/game/status")
def game_status() -> dict:
    return {
        "game": "Animal Company",
        "connection": "not_connected",
        "integration": "unavailable",
        "supported_actions": [],
        "features": {
            "join_room": False,
            "player_movement": False,
            "spawn_items": False,
            "read_game_state": False,
        },
        "message": (
            "No verified official game integration is configured. "
            "The companion can handle voice and confirmations, but cannot "
            "control an Animal Company session."
        ),
    }


@router.post("/game/command")
def game_command(command: GameCommand) -> None:
    # Fail closed: never pretend a request reached the game.
    raise HTTPException(
        status_code=501,
        detail=(
            "Game control is unavailable: no authorized Animal Company "
            "integration is configured. No in-game action was performed."
        ),
    )
