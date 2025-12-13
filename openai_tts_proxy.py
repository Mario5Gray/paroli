import json
import os
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

PAROLI_URL = os.getenv("PAROLI_URL", "http://localhost:8848/api/v1/synthesise")
VOICE_MAP = json.loads(os.getenv("VOICE_MAP", "{}"))  # e.g. {"alloy": 0, "amber": 1}
API_KEY = os.getenv("OPENAI_API_KEY")  # Optional shared secret; set to enable auth

app = FastAPI()


class SpeechRequest(BaseModel):
    model: str  # required by OpenAI; not used here
    input: str
    voice: Optional[str] = None
    response_format: Optional[str] = None  # "opus"/"ogg" (default) or "pcm"/"wav"
    speed: Optional[float] = None          # 1.0 = normal; >1 faster, <1 slower


def _map_format(fmt: Optional[str]):
    fmt = (fmt or "opus").lower()
    if fmt in ("opus", "ogg"):
        return "opus", "audio/ogg"
    if fmt in ("pcm", "wav", "raw"):
        return "pcm", "application/octet-stream"
    raise HTTPException(status_code=400, detail="Unsupported response_format")


@app.post("/v1/audio/speech")
async def tts(req: SpeechRequest, authorization: Optional[str] = Header(default=None)):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    audio_format, media_type = _map_format(req.response_format)
    speaker_id = VOICE_MAP.get(req.voice) if req.voice else None

    payload = {"text": req.input, "audio_format": audio_format}
    if speaker_id is not None:
        payload["speaker_id"] = speaker_id
    if req.speed and req.speed > 0:
        # Paroli length_scale: <1 = faster, >1 = slower (approx)
        payload["length_scale"] = max(0.2, min(5.0, 1.0 / req.speed))

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(PAROLI_URL, json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Paroli error: {resp.text}",
            )
        return StreamingResponse(resp.aiter_bytes(), media_type=media_type)


@app.get("/health")
async def health():
    return {"status": "ok"}

