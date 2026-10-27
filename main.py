"""Operational authenticated web-chat channel for the Voice AI Agency.

This module DOES NOT pretend to implement telephony, STT, TTS or social
channels. It is a usable foundation backed by real LLM API requests.
"""
from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from typing import Literal

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from languages import detect_language_from_text, get_all_languages, get_lang_config, LANGUAGES


APP_ROOT = Path(__file__).resolve().parent
PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions",
             "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "openai": ("https://api.openai.com/v1/chat/completions",
               "OPENAI_API_KEY", "gpt-4o-mini"),
    "deepseek": ("https://api.deepseek.com/chat/completions",
                 "DEEPSEEK_API_KEY", "deepseek-chat"),
}
app = FastAPI(title="Voice AI Agency · Web Chat", version="0.2.0")
_usage: dict[str, deque[float]] = defaultdict(deque)
_usage_lock = Lock()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, content: str) -> str:
        if not content.strip():
            raise ValueError("Message content must not be blank")
        return content


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=12)
    language: str | None = None

    @field_validator("messages")
    @classmethod
    def limit_conversation_size(cls, messages: list[Message]) -> list[Message]:
        # Bound total provider input, not just each individual message.
        if sum(len(message.content) for message in messages) > 16000:
            raise ValueError("Conversation exceeds 16000 characters")
        return messages


class ChatResponse(BaseModel):
    reply: str
    language: str
    provider: str


def _authorize(authorization: str | None):
    expected = os.environ.get("VOICE_AGENCY_API_TOKEN", "")
    if not expected:
        raise HTTPException(503, "Service authentication is not configured")
    actual = authorization or ""
    if not hmac.compare_digest(actual, "Bearer " + expected):
        raise HTTPException(401, "Invalid API token")


def _limit_requests(ip_address: str):
    now = time.monotonic()
    with _usage_lock:
        # Prune idle clients before allocating a new deque. Otherwise a
        # distributed stream of one-off source IPs grows this process forever.
        if ip_address not in _usage and len(_usage) >= 4096:
            stale = [client for client, times in _usage.items()
                     if not times or now - times[-1] >= 60]
            for client in stale:
                del _usage[client]
            if len(_usage) >= 4096:
                raise HTTPException(429, "Service is busy; try again shortly")
        visits = _usage[ip_address]
        while visits and now - visits[0] >= 60:
            visits.popleft()
        if len(visits) >= 20:
            raise HTTPException(429, "Too many requests; try again shortly")
        visits.append(now)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/languages")
def languages():
    return get_all_languages()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    page = (APP_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(page, headers={
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    })


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request,
               authorization: str | None = Header(default=None)):
    _authorize(authorization)
    if body.messages[-1].role != "user":
        raise HTTPException(422, "The final message must be from the user")
    _limit_requests(request.client.host if request.client else "unknown")

    if body.language is not None and body.language not in LANGUAGES:
        raise HTTPException(422, "Unsupported language")
    language = body.language or detect_language_from_text(body.messages[-1].content)
    profile = get_lang_config(language)

    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider not in PROVIDERS:
        raise HTTPException(503, "LLM_PROVIDER must be groq, openai, or deepseek")
    endpoint, key_name, default_model = PROVIDERS[provider]
    key = os.environ.get(key_name)
    if not key:
        raise HTTPException(503, f"{provider} credentials are not configured")

    system_prompt = (
        profile.system_prompt + "\n"
        "Do not claim to have taken actions, scheduled callbacks, contacted an "
        "employee or accessed business systems. If you cannot verify an answer, "
        "say so. Never request passwords, payment-card data or identity documents."
    )
    payload = {
        "model": os.environ.get("LLM_MODEL", default_model),
        "temperature": 0.4,
        "max_tokens": 350,
        "messages": [
            {"role": "system", "content": system_prompt},
            *[msg.model_dump() for msg in body.messages],
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=False) as client:
            response = await client.post(
                endpoint,
                headers={"Authorization": "Bearer " + key,
                         "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Missing response content")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as exc:
        # Do not echo remote API response bodies (may include user input).
        raise HTTPException(502, "The language provider is unavailable") from exc
    return ChatResponse(reply=content.strip(), language=language, provider=provider)


if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8000")))
