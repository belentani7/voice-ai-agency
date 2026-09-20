"""Entrypoint minimo para desplegar en Vercel (framework: python).

Vercel abortaba el build con:
  Error: No python entrypoint found. Set "tool.vercel.entrypoint" in
  pyproject.toml or define an entrypoint in one of: app.py, index.py,
  server.py, main.py, ...

Este fichero existe para desbloquear el deploy. Expone el esqueleto de la
plataforma (config.py + languages.py) por HTTP. NO es el backend completo
descrito en el README: canales (WhatsApp/Instagram/Twilio), STT/TTS y CRM
siguen pendientes.
"""

from fastapi import FastAPI

from config import LLMConfig, VoiceConfig

app = FastAPI(title="Voice AI Agency", version="0.1.0")

_llm = LLMConfig()
_voice = VoiceConfig()


@app.get("/")
def root():
    return {
        "service": "voice-ai-agency",
        "status": "ok",
        "version": "0.1.0",
        "note": "entrypoint minimo: desbloquea el deploy en Vercel",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/config")
def config_summary():
    """Config no sensible: proveedores y motores, sin claves."""
    return {
        "llm_provider": _llm.provider,
        "llm_model": _llm.model,
        "llm_providers": sorted(_llm.providers.keys()),
        "stt_engine": _voice.stt_engine,
    }
