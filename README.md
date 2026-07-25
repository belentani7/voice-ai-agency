# Voice AI Agency Platform

**Plataforma multi-canal de agentes de voz AI para PYMEs en LATAM + España/Portugal**

## Qué es

Un framework completo para crear, desplegar y gestionar agentes de voz AI que atienden clientes por WhatsApp, Instagram DM y llamadas telefónicas. Multiidioma (PT-BR, PT-PT, ES, CA, EN), costo operativo ~$0, escalable a cientos de clientes.

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                  ADMIN DASHBOARD                     │
│              (Next.js + Tailwind CSS)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Clients  │ │  Bots    │ │ Analytics│ │  CRM   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└───────────────────────┬─────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────┐
│                  BACKEND (FastAPI)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Channels │ │ Voice    │ │   LLM    │ │  CRM   │ │
│  │ WA/IG/   │ │ Processor│ │  Router  │ │ Engine │ │
│  │ Phone    │ │ STT/TTS  │ │ 5 models │ │Twenty  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────┘
```

## Canales soportados

| Canal | API | Costo | Status |
|-------|-----|-------|--------|
| WhatsApp | Meta Cloud API | 1000 gratis/mes | Listo |
| Instagram DM | instagrapi | Gratis (scraping) | Listo |
| Llamadas | Twilio Voice | ~$0.01/min | Listo |
| Telegram | Bot API | Gratis | Planificado |
| Web Chat | WebSocket | Gratis | Planificado |

## Stack

- **Backend**: Python 3.10+, FastAPI, uvicorn
- **STT**: OpenAI Whisper (local) o Groq Whisper API
- **LLM**: Groq (Llama 3.3 70B) / OpenAI / DeepSeek / Gemini
- **TTS**: Edge-TTS (Microsoft Neural voices, gratis)
- **Audio**: pydub + ffmpeg
- **CRM**: Twenty / NocoBase (via MCP)
- **Dashboard**: HTML/CSS/JS vanilla (sin build step)
- **Deploy**: Docker Compose, VPS $5/mes

## Costo operativo por cliente

| Componente | Costo |
|------------|-------|
| Groq LLM (30 RPM free) | $0 |
| Edge-TTS | $0 |
| Whisper (local) | $0 |
| WhatsApp (1000 free/mes) | $0 |
| VPS compartido | ~$1-2/cliente |
| **Total** | **~$1-2/cliente/mes** |
| **Precio de venta** | **$150-500/cliente/mes** |
| **Margen** | **97-99%** |

## Quick Start

```bash
# 1. Clonar e instalar
git clone <repo>
cd voice-ai-agency
pip install -r requirements.txt

# 2. Configurar
cp .env.example .env
# Editar .env con tus API keys

# 3. Ejecutar
python main.py

# Dashboard: http://localhost:8000/dashboard
# API: http://localhost:8000/docs
```

## Estructura

```
voice-ai-agency/
├── main.py                    # FastAPI entry point
├── config.py                  # Configuration management
├── voice_processor.py         # STT + TTS pipeline
├── llm_chat.py                # Multi-LLM router
├── languages.py               # 5 idiomas + system prompts
├── crm_engine.py              # CRM integration (Twenty/NocoBase)
├── channels/
│   ├── whatsapp.py            # WhatsApp Cloud API
│   ├── instagram.py           # Instagram DM (instagrapi)
│   └── phone.py               # Twilio Voice
├── dashboard/
│   └── index.html             # Admin dashboard (single-page)
├── templates/
│   └── bot-config.json        # Plantilla de configuración de bot
├── docs/
│   ├── DEPLOY-GUIA.md         # Guía de despliegue
│   └── BUSINESS-MODEL.md      # Modelo de negocio
├── docker-compose.yml         # Deploy completo
├── Dockerfile                 # Backend container
├── requirements.txt           # Dependencias Python
├── .env.example               # Template de configuración
├── setup.py                   # Instalador automático
└── Makefile                   # Comandos comunes
```

## Licencia

MIT — usar, modificar, vender. Sin restricciones.
