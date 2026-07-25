"""Configuration management for Voice AI Agency Platform."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    api_key: str = ""
    max_tokens: int = 250
    temperature: float = 0.7
    top_p: float = 0.9

    # Multi-provider fallback
    providers: dict = field(default_factory=lambda: {
        "groq": {"model": "llama-3.3-70b-versatile", "rpm": 30},
        "openai": {"model": "gpt-4o-mini", "rpm": 500},
        "deepseek": {"model": "deepseek-chat", "rpm": 60},
        "gemini": {"model": "gemini-2.0-flash", "rpm": 60},
        "nvidia": {"model": "meta/llama-3.3-70b-instruct", "rpm": 40},
    })


@dataclass
class VoiceConfig:
    stt_engine: str = "whisper"  # whisper | groq_whisper
    whisper_model: str = "base"  # tiny | base | small | medium | large
    tts_engine: str = "edge-tts"  # edge-tts | openai-tts
    audio_format: str = "wav"
    sample_rate: int = 16000


@dataclass
class WhatsAppConfig:
    phone_number_id: str = ""
    access_token: str = ""
    verify_token: str = ""
    api_version: str = "v19.0"


@dataclass
class InstagramConfig:
    username: str = ""
    password: str = ""
    session_file: str = "session/instagram.json"


@dataclass
class TwilioConfig:
    account_sid: str = ""
    auth_token: str = ""
    phone_number: str = ""
    webhook_url: str = ""


@dataclass
class CRMConfig:
    provider: str = "twenty"  # twenty | nocobase | wa-crm
    url: str = ""
    api_key: str = ""
    mcp_enabled: bool = True


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    public_url: str = ""  # For webhooks (use ngrok in dev)
    debug: bool = False
    log_level: str = "INFO"
    dashboard_enabled: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    instagram: InstagramConfig = field(default_factory=InstagramConfig)
    twilio: TwilioConfig = field(default_factory=TwilioConfig)
    crm: CRMConfig = field(default_factory=CRMConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    # Paths
    data_dir: str = "data"
    session_dir: str = "session"
    audio_dir: str = "audio_cache"
    logs_dir: str = "logs"

    # Bot behavior
    max_conversation_history: int = 10
    max_voice_duration_seconds: int = 60
    dedup_window_size: int = 5000
    polling_interval_seconds: int = 5
    max_threads: int = 10
    messages_per_thread: int = 5


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    config = AppConfig()

    # LLM
    config.llm.provider = os.getenv("LLM_PROVIDER", config.llm.provider)
    config.llm.model = os.getenv("LLM_MODEL", config.llm.model)
    config.llm.api_key = os.getenv("GROQ_API_KEY", "")
    config.openai_key = os.getenv("OPENAI_API_KEY", "")
    config.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    config.gemini_key = os.getenv("GEMINI_API_KEY", "")

    # Voice
    config.voice.stt_engine = os.getenv("STT_ENGINE", config.voice.stt_engine)
    config.voice.whisper_model = os.getenv("WHISPER_MODEL", config.voice.whisper_model)

    # WhatsApp
    config.whatsapp.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    config.whatsapp.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    config.whatsapp.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "voice-ai-agency-verify")

    # Instagram
    config.instagram.username = os.getenv("INSTAGRAM_USERNAME", "")
    config.instagram.password = os.getenv("INSTAGRAM_PASSWORD", "")

    # Twilio
    config.twilio.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    config.twilio.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    config.twilio.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")

    # CRM
    config.crm.url = os.getenv("CRM_URL", "")
    config.crm.api_key = os.getenv("CRM_API_KEY", "")

    # Server
    config.server.host = os.getenv("HOST", config.server.host)
    config.server.port = int(os.getenv("PORT", str(config.server.port)))
    config.server.public_url = os.getenv("PUBLIC_URL", "")
    config.server.debug = os.getenv("DEBUG", "false").lower() == "true"

    # Create directories
    for d in [config.data_dir, config.session_dir, config.audio_dir, config.logs_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    return config


# Singleton
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
