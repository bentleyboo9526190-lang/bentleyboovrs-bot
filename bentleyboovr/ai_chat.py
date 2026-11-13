from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()

SYSTEM_PROMPT = (
    "You are BentleyBooVR, a friendly, upbeat gaming companion. "
    "Be helpful, curious, and concise. You can chat about games and everyday "
    "questions. Be honest about your limits: you cannot control Animal Company, "
    "change game data, or perform actions inside the game. Never claim that you did."
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatBody(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


@router.get("/chat", response_class=HTMLResponse)
def chat_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BentleyBooVR AI Chat</title>
<style>
body{font-family:system-ui,sans-serif;max-width:720px;margin:24px auto;padding:0 16px;background:#101827;color:#f4f7fb}
h1{margin-bottom:4px}p{color:#c5d0df}
#log{height:55vh;min-height:280px;overflow:auto;background:#1c2a3e;border-radius:14px;padding:14px}
.msg{padding:10px 12px;margin:8px 0;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}
.user{background:#29496b;margin-left:12%}.assistant{background:#26384b;margin-right:12%}
textarea{box-sizing:border-box;width:100%;min-height:72px;margin-top:12px;padding:12px;border-radius:10px;font:inherit}
button{font:inherit;font-weight:650;padding:11px 16px;margin:8px 6px 0 0;border:0;border-radius:10px;background:#8fc7ff;color:#102033}
button:disabled{opacity:.5}#status{min-height:24px}
</style></head>
<body>
<h1>🐾 BentleyBooVR</h1><p>Chat with your AI companion. This is a chat prototype, not an in-game connection.</p>
<div id="log" aria-live="polite"><div class="msg assistant">Hey! BentleyBooVR here. What should we talk about?</div></div>
<textarea id="message" maxlength="2000" placeholder="Message BentleyBooVR…"></textarea>
<div><button id="send">Send</button><button id="mic">🎙️ Speak</button><button id="clear">New chat</button></div>
<p id="status" role="status">Ready.</p>
<script>
const log=document.getElementById('log'), box=document.getElementById('message'), status=document.getElementById('status');
let messages=[];
function add(role,text){const el=document.createElement('div');el.className='msg '+role;el.textContent=text;log.appendChild(el);log.scrollTop=log.scrollHeight;}
async function send(){
 const text=box.value.trim();if(!text)return;
 messages.push({role:'user',content:text});add('user',text);box.value='';
 document.getElementById('send').disabled=true;status.textContent='BentleyBooVR is thinking…';
 try{
  const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:messages.slice(-20)})});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||'Chat request failed');
  messages.push({role:'assistant',content:data.reply});add('assistant',data.reply);status.textContent='Ready.';
  try{const speech=await fetch('/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:data.reply})});if(speech.ok){const audio=new Audio(URL.createObjectURL(await speech.blob()));audio.play().catch(()=>{});}}
  catch(e){}
 }catch(error){messages.pop();status.textContent=error.message;}
 finally{document.getElementById('send').disabled=false;box.focus();}
}
document.getElementById('send').addEventListener('click',send);
box.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
document.getElementById('clear').addEventListener('click',()=>{messages=[];log.innerHTML='';add('assistant','Fresh chat! What is on your mind?');status.textContent='New chat started.';});
document.getElementById('mic').addEventListener('click',()=>{
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!SR){status.textContent='Voice input is not supported in this browser. Type your message instead.';return;}
 const rec=new SR();rec.lang='en-US';rec.interimResults=false;status.textContent='Listening…';
 rec.onresult=e=>{box.value=e.results[0][0].transcript;send();};
 rec.onerror=e=>status.textContent='Microphone issue: '+e.error;rec.start();
});
</script></body></html>"""


@router.post("/api/chat")
async def chat(body: ChatBody) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI chat is not configured. Set OPENAI_API_KEY on the computer running BentleyBooVR.",
        )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[message.model_dump() for message in body.messages],
        ],
        "temperature": 0.7,
        "max_tokens": 350,
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            result = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not reach the AI chat service.")

    if result.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="The AI chat service returned an error. Check the API account and server configuration.",
        )
    try:
        reply = result.json()["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, AttributeError):
        raise HTTPException(status_code=502, detail="The AI chat service returned an unexpected response.")
    if not reply:
        raise HTTPException(status_code=502, detail="The AI chat service returned an empty reply.")
    return {"reply": reply}
