from __future__ import annotations

from datetime import datetime, timezone
import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
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


@app.get("/voice", response_class=HTMLResponse)
def voice_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BentleyBooVR Voice</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 620px; margin: 40px auto; padding: 0 18px; background: #101827; color: #f4f7fb; }
    h1 { margin-bottom: 8px; }
    p { color: #c5d0df; }
    button, input { font: inherit; border-radius: 10px; padding: 12px; margin: 6px 4px 6px 0; }
    input { width: min(95%, 420px); }
    button { border: 0; cursor: pointer; background: #8fc7ff; color: #102033; font-weight: 650; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    #status, #heard { padding: 12px; background: #1c2a3e; border-radius: 10px; min-height: 24px; }
    #confirm { display: none; }
    .settings { margin: 18px 0; padding: 14px; background: #1c2a3e; border-radius: 10px; }
    label { display: block; margin: 8px 0; color: #dce7f5; }
    select { font: inherit; padding: 8px; border-radius: 8px; max-width: 100%; }
  </style>
</head>
<body>
  <h1>🐾 BentleyBooVR</h1>
  <p>AI-generated voice prototype: say a request, hear BentleyBooVR repeat it, then choose yes or no.</p>
  <input id="requestText" maxlength="300" placeholder="Type a request, or use the microphone">
  <div class="settings">
    <strong>Voice settings</strong>
    <label for="voiceSelect">Device voice</label>
    <select id="voiceSelect"><option value="">Loading available voices…</option></select>
    <label for="pitch">Pitch: <span id="pitchValue">0.75</span></label>
    <input id="pitch" type="range" min="0.5" max="1.2" step="0.05" value="0.75">
    <label for="rate">Speaking speed: <span id="rateValue">0.9</span></label>
    <input id="rate" type="range" min="0.7" max="1.1" step="0.05" value="0.9">
  </div>
  <div>
    <button id="micButton">🎙️ Speak</button>
    <button id="sendButton">Send request</button>
  </div>
  <p id="status" role="status">Ready. Microphone access starts only when you press Speak.</p>
  <p id="heard"></p>
  <div id="confirm">
    <p>Do you want this?</p>
    <button id="yesButton">Yes</button>
    <button id="noButton">No</button>
  </div>
  <script>
    const input = document.getElementById("requestText");
    const statusBox = document.getElementById("status");
    const heardBox = document.getElementById("heard");
    const confirmBox = document.getElementById("confirm");
    let pendingId = null;
    const voiceSelect = document.getElementById("voiceSelect");
    const pitchControl = document.getElementById("pitch");
    const rateControl = document.getElementById("rate");
    document.getElementById("pitchValue").textContent = pitchControl.value;
    document.getElementById("rateValue").textContent = rateControl.value;
    pitchControl.addEventListener("input", () => document.getElementById("pitchValue").textContent = pitchControl.value);
    rateControl.addEventListener("input", () => document.getElementById("rateValue").textContent = rateControl.value);

    function loadVoices() {
      if (!("speechSynthesis" in window)) {
        voiceSelect.innerHTML = '<option value="">Speech output unavailable</option>';
        return;
      }
      const voices = window.speechSynthesis.getVoices();
      voiceSelect.innerHTML = '<option value="">System default voice</option>';
      voices.forEach((voice, index) => {
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = voice.name + " (" + voice.lang + ")";
        voiceSelect.appendChild(option);
      });
    }
    if ("speechSynthesis" in window) {
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    let currentAudio = null;
    async function speak(text) {
      if (currentAudio) {
        currentAudio.pause();
        URL.revokeObjectURL(currentAudio.src);
        currentAudio = null;
      }
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      try {
        const response = await fetch("/speech", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({text})
        });
        if (!response.ok) {
          const problem = await response.json().catch(() => ({}));
          throw new Error(problem.detail || "AI voice is not configured");
        }
        const audioBlob = await response.blob();
        currentAudio = new Audio(URL.createObjectURL(audioBlob));
        currentAudio.onended = () => {
          if (currentAudio) URL.revokeObjectURL(currentAudio.src);
          currentAudio = null;
        };
        await currentAudio.play();
        statusBox.textContent = "Speaking with BentleyBooVR's AI voice. This voice is AI-generated.";
      } catch (error) {
        statusBox.textContent = error.message + ". Using your device voice instead.";
        if ("speechSynthesis" in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = Number(rateControl.value);
          utterance.pitch = Number(pitchControl.value);
          const voices = window.speechSynthesis.getVoices();
          if (voiceSelect.value !== "" && voices[Number(voiceSelect.value)]) {
            utterance.voice = voices[Number(voiceSelect.value)];
          }
          window.speechSynthesis.speak(utterance);
        }
      }
    }

    document.getElementById("micButton").addEventListener("click", () => {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        statusBox.textContent = "Speech recognition is not supported in this browser. You can type a request instead.";
        return;
      }
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      statusBox.textContent = "Listening…";
      recognition.onresult = event => {
        input.value = event.results[0][0].transcript;
        statusBox.textContent = "I heard: " + input.value;
      };
      recognition.onerror = event => statusBox.textContent = "Microphone issue: " + event.error;
      recognition.onend = () => {
        if (statusBox.textContent === "Listening…") statusBox.textContent = "Didn't catch that. Try again or type your request.";
      };
      recognition.start();
    });

    document.getElementById("sendButton").addEventListener("click", async () => {
      const text = input.value.trim();
      if (!text) {
        statusBox.textContent = "Please say or type a request first.";
        return;
      }
      try {
        const response = await fetch("/request", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({text})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Request failed");
        pendingId = data.request_id;
        heardBox.textContent = data.spoken_response;
        confirmBox.style.display = "block";
        statusBox.textContent = "Waiting for your yes or no.";
        speak(data.spoken_response);
      } catch (error) {
        statusBox.textContent = "Could not contact BentleyBooVR: " + error.message;
      }
    });

    async function confirm(approved) {
      if (!pendingId) return;
      try {
        const response = await fetch("/confirm", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({request_id: pendingId, approved})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Confirmation failed");
        statusBox.textContent = data.message;
        speak(data.message);
        pendingId = null;
        confirmBox.style.display = "none";
      } catch (error) {
        statusBox.textContent = "Could not save your answer: " + error.message;
      }
    }
    document.getElementById("yesButton").addEventListener("click", () => confirm(true));
    document.getElementById("noButton").addEventListener("click", () => confirm(false));
  </script>
</body>
</html>"""


@app.post("/speech")
async def generate_speech(body: RequestBody) -> Response:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI voice is not configured. Set OPENAI_API_KEY on the computer running BentleyBooVR.",
        )

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Speech text cannot be empty.")

    payload = {
        "model": "gpt-4o-mini-tts",
        "voice": "onyx",
        "input": text[:1200],
        "instructions": (
            "Speak as BentleyBooVR, a friendly gaming companion. Use a warm, "
            "confident, lower-register voice, clear pronunciation, and a relaxed pace. "
            "Do not sound angry or intimidating."
        ),
        "response_format": "mp3",
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            result = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="The AI voice service could not be reached.")

    if result.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="The AI voice service returned an error. Check the server configuration and API account.",
        )
    return Response(content=result.content, media_type="audio/mpeg")


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
        "spoken_response": f"BentleyBooVR here. I heard your request: {requested_action}. Should I proceed?",
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


# Animal Company game bridge: safe status reporting only until an authorized
# integration is available. It never sends commands to the game.
from game_bridge import router as game_router

app.include_router(game_router)
