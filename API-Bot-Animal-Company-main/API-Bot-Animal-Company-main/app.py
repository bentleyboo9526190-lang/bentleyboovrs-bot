import os
import json
import uuid
import logging
import asyncio
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# =========================
# Config
# =========================
TARGET_BASE = os.getenv("TARGET_BASE", "https://animalcompany.us-east1.nakamacloud.io")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # leave blank to disable
LOG_DIR = os.getenv("LOG_DIR", "request_logs")
ZIP_FOLDER = os.path.abspath(os.getenv("ZIP_FOLDER", "data"))
ZIP_FILENAME = os.getenv("ZIP_FILENAME", "game-data-prod.zip")

TIMEOUT = httpx.Timeout(20.0, connect=10.0)
CLIENT = httpx.AsyncClient(timeout=TIMEOUT, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
APP_ID = os.getenv("APP_ID", "proxy-" + uuid.uuid4().hex[:8])

os.makedirs(LOG_DIR, exist_ok=True)

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("proxy")

def _redact_headers(hdrs: Dict[str, str]) -> Dict[str, str]:
    out = {}
    for k, v in hdrs.items():
        kl = k.lower()
        if kl in ("authorization", "cookie", "x-api-key", "proxy-authorization"):
            out[k] = "***redacted***"
        else:
            out[k] = v
    return out

async def _post_webhook(payload: Dict[str, Any]) -> None:
    if not WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            await c.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        logger.debug(f"Webhook failed: {e}")

# =========================
# App
# =========================
app = FastAPI(title="AC Proxy", version="2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# ------------- Middleware: structured request/response logging (non-blocking) -------------
@app.middleware("http")
async def access_log(request: Request, call_next):
    req_id = uuid.uuid4().hex[:8]
    # Read body without breaking downstream by buffering and re-injecting
    body_bytes = await request.body()
    async def receive() -> dict:
        return {"type": "http.request", "body": body_bytes, "more_body": False}
    request._receive = receive  # type: ignore

    started = datetime.utcnow().isoformat() + "Z"
    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.exception("Handler exception")
        await _post_webhook({"content": f"❌ {APP_ID} {request.method} {request.url.path} raised {e}"})
        return JSONResponse({"error": "Internal Server Error"}, status_code=500)

    try:
        entry = {
            "id": req_id,
            "ts": started,
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "req_headers": _redact_headers(dict(request.headers)),
            "req_body_preview": body_bytes[:4096].decode("utf-8", errors="ignore"),
            "status": response.status_code,
        }
        log_path = os.path.join(LOG_DIR, f"{request.url.path.strip('/').replace('/','_') or 'root'}.ndjson")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return response

# =========================
# Helpers
# =========================
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade"
}

def _prepare_forward_headers(req: Request) -> Dict[str, str]:
    headers = {k: v for k, v in req.headers.items() if k.lower() not in HOP_BY_HOP and k.lower() != "host"}
    # upstream host is set by httpx; don't override Host unless you must
    return headers

async def _stream_to_client(up: httpx.Response) -> StreamingResponse:
    # Stream upstream response to client
    headers = {k: v for k, v in up.headers.items() if k.lower() not in HOP_BY_HOP}
    async def iter_bytes():
        async for chunk in up.aiter_bytes():
            yield chunk
    return StreamingResponse(iter_bytes(), status_code=up.status_code, headers=headers, media_type=headers.get("content-type"))

async def forward_request(path: str, request: Request) -> Response:
    # Normalize and join URL
    path = path.lstrip("/")
    url = f"{TARGET_BASE}/{path}"
    headers = _prepare_forward_headers(request)
    method = request.method.upper()

    try:
        if method in ("GET", "HEAD"):
            upstream = await CLIENT.request(method, url, headers=headers, params=request.query_params)
            return await _stream_to_client(upstream)

        # For methods with body
        body = await request.body()
        upstream = await CLIENT.request(
            method, url, headers=headers, params=request.query_params, content=body
        )
        return await _stream_to_client(upstream)

    except httpx.HTTPError as e:
        logger.warning(f"Upstream error {method} {url}: {e}")
        await _post_webhook({"content": f"⚠️ Upstream error {method} {url}: {e}"})
        return JSONResponse({"error": "Proxy Error", "details": str(e)}, status_code=502)

# =========================
# Health & static
# =========================
@app.get("/health")
async def health():
    return {"ok": True, "app": APP_ID}

@app.get("/data/game-data-prod.zip")
async def serve_zip():
    p = os.path.join(ZIP_FOLDER, ZIP_FILENAME)
    if not os.path.exists(p):
        return PlainTextResponse("ZIP not found", status_code=404)
    return FileResponse(p, filename=ZIP_FILENAME, media_type="application/zip")

# =========================
# Econ passthrough (local file)
# =========================
@app.get("/econ/items")
async def econ_items():
    try:
        with open("econ_gameplay_items.json", "r", encoding="utf-8") as f:
            return JSONResponse(json.load(f))
    except Exception as e:
        return JSONResponse({"error": f"Failed to load JSON: {e}"}, status_code=500)

# =========================
# Specific RPC examples (kept)
# =========================
@app.post("/v2/rpc/attest.start")
async def rpc_attest_start(request: Request):
    return await forward_request("v2/rpc/attest.start", request)

@app.post("/v2/rpc/avatar.update")
async def rpc_avatar_update(request: Request):
    return await forward_request("v2/rpc/avatar.update", request)

@app.post("/v2/rpc/purchase.stashUpgrade")
async def rpc_purchase_stash_upgrade(request: Request):
    return await forward_request("v2/rpc/purchase.stashUpgrade", request)

@app.post("/v2/rpc/updateWalletSoftCurrency")
async def rpc_update_wallet_soft(request: Request):
    return await forward_request("v2/rpc/updateWalletSoftCurrency", request)

# =========================
# WebSocket bridge
# =========================
@app.websocket("/ws")
async def ws_bridge(client_ws: WebSocket):
    await client_ws.accept()
    token = client_ws.query_params.get("token")
    if not token:
        await client_ws.close(code=1008)
        return

    qs = {
        "lang": "en",
        "status": "True",
        "token": token,
    }
    target = f"wss://{urllib.parse.urlparse(TARGET_BASE).netloc}/ws?{urllib.parse.urlencode(qs)}"

    import websockets
    try:
        async with websockets.connect(target, max_size=None) as upstream:
            async def c2u():
                try:
                    while True:
                        msg = await client_ws.receive_text()
                        await upstream.send(msg)
                except (WebSocketDisconnect, Exception):
                    await upstream.close()

            async def u2c():
                try:
                    async for msg in upstream:
                        if isinstance(msg, bytes):
                            await client_ws.send_bytes(msg)
                        else:
                            await client_ws.send_text(msg)
                except Exception:
                    with contextlib.suppress(Exception):
                        await client_ws.close()

            await asyncio.gather(c2u(), u2c())
    except Exception as e:
        await client_ws.send_text(f"Error: {e}")
        await client_ws.close()

# =========================
# Account / Session helpers
# =========================
@app.post("/v2/account/session/refresh")
async def session_refresh(request: Request):
    return await forward_request("v2/account/session/refresh", request)

@app.post("/v2/account/authenticate/device")
async def auth_device(request: Request):
    return await forward_request("v2/account/authenticate/device", request)

@app.post("/v2/account/authenticate/custom")
async def auth_custom(request: Request):
    return await forward_request("v2/account/authenticate/custom", request)

# =========================
# Generic pass-throughs (covers most remaining endpoints)
# =========================
@app.api_route("/v2/{full_path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def proxy_v2(full_path: str, request: Request):
    return await forward_request(f"v2/{full_path}", request)

@app.api_route("/api/{full_path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def proxy_api(full_path: str, request: Request):
    return await forward_request(f"api/{full_path}", request)

# =========================
# Startup / Shutdown
# =========================
@app.on_event("shutdown")
async def _shutdown():
    await CLIENT.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "7000")), reload=False)
