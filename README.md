# Voice AI Agency Platform

**Prototipo de configuración y selección de idioma para futuros agentes de voz.**

## Qué es

Este repositorio contiene hoy `languages.py`, `config.py` y pruebas de enrutamiento de voz en PT-BR, PT-PT, ES, CA y EN. Define voces y textos por idioma, detecta señales en mensajes y rechaza locales sin voz configurada. No contiene todavía servidor, integraciones de canales, síntesis o reconocimiento de audio ejecutables, panel ni despliegue.

## Arquitectura prevista

El siguiente diagrama es una propuesta de producto, no una descripción de módulos implementados en esta rama.

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

## Canales propuestos

| Canal | API | Costo | Status |
|-------|-----|-------|--------|
| WhatsApp | Meta Cloud API | Por validar | Planificado |
| Instagram DM | Por decidir | Por validar | Planificado |
| Llamadas | Twilio Voice | Por validar | Planificado |
| Telegram | Bot API | Por validar | Planificado |
| Web Chat | WebSocket | Por validar | Planificado |

## Stack propuesto

- **Módulo actual**: Python 3.10+, biblioteca estándar
- **Backend futuro**: FastAPI, uvicorn
- **STT**: OpenAI Whisper (local) o Groq Whisper API
- **LLM**: Groq (Llama 3.3 70B) / OpenAI / DeepSeek / Gemini
- **TTS**: Edge-TTS (Microsoft Neural voices, gratis)
- **Audio**: pydub + ffmpeg
- **CRM**: Twenty / NocoBase (via MCP)
- **Dashboard futuro**: por diseñar
- **Despliegue futuro**: por diseñar y verificar

## Costes

No hay despliegue ni medición por cliente en este repositorio. Precios, cuotas de proveedores y márgenes deberán estimarse con contratos vigentes y pruebas de carga antes de utilizarlos en una oferta comercial.

## Probar lo que existe

```bash
# Clonar el repositorio y ejecutar las pruebas sin dependencias externas
git clone https://github.com/belentani7/voice-ai-agency.git
cd voice-ai-agency
python -m unittest discover -s tests -p 'test_*.py' -v
```

Para usar el módulo desde Python, importa `detect_language_from_text`, `get_lang_config` o `resolve_supported_language` de `languages.py`. El idioma preferido debe ser uno de los locales configurados; un código regional sin voz verificada genera `ValueError`.

## Estructura

```
voice-ai-agency/
├── languages.py               # Locales, voces previstas y detección de texto
├── config.py                  # Estructuras de configuración para integraciones futuras
├── tests/test_languages.py    # Regresiones de dialectos y locales
├── requirements.txt           # Sin dependencias activas todavía
└── .github/workflows/ci.yml  # Compilación y pruebas del módulo
```

## Licencia

MIT — usar, modificar, vender. Sin restricciones.
