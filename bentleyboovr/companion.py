from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="BentleyBooVR Companion",
    description="A local prototype for request repetition and yes/no confirmation.",
    version="0.1.0",
)

# Prototype-only in-memory storage. Pending requests disappear when the server restarts.
pending_requests: dict[str, dict] = {}


class RequestBody(BaseModel):
    text: str = Field(min_length=1, max_length=300)


class ConfirmationBody(BaseModel):
    request_id: str
    approved: bool


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "BentleyBooVR Companion"}


@app.post("/request")
def create_request(body: RequestBody) -> dict:
    requested_action = body.text.strip()
    if not requested_action:
        raise HTTPException(status_code=400, detail="Please provide a request.")

    request_id = str(uuid4())
    pending_requests[request_id] = {
        "text": requested_action,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "awaiting_confirmation",
    }

    return {
        "request_id": request_id,
        "heard": requested_action,
        "spoken_response": f"You asked me to {requested_action}. Do you want this?",
        "status": "awaiting_confirmation",
    }


@app.post("/confirm")
def confirm_request(body: ConfirmationBody) -> dict:
    request = pending_requests.get(body.request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found or already cleared.")

    request["status"] = "approved" if body.approved else "declined"
    request["confirmed_at"] = datetime.now(timezone.utc).isoformat()

    if body.approved:
        message = "Confirmed. This prototype has recorded your approval, but it has not performed an in-game action."
    else:
        message = "Okay, I won't proceed. Your request was declined."

    result = {
        "request_id": body.request_id,
        "requested_action": request["text"],
        "status": request["status"],
        "message": message,
    }
    del pending_requests[body.request_id]
    return result
