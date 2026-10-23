"""Multi-language support for Voice AI Agency Platform.

5 languages with per-language:
- Edge-TTS voice IDs
- Whisper language detection mapping
- System prompts (personality + behavior)
- Greeting messages
- Fallback messages
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LanguageConfig:
    code: str
    name: str
    edge_tts_voice: str
    whisper_language: str
    system_prompt: str
    greeting: str
    fallback: str
    # Text message detection keywords
    detection_keywords: list


LANGUAGES: Dict[str, LanguageConfig] = {
    "pt-BR": LanguageConfig(
        code="pt-BR",
        name="Português (Brasil)",
        edge_tts_voice="pt-BR-FranciscaNeural",
        whisper_language="portuguese",
        system_prompt="""Você é um assistente virtual inteligente e prestativo de uma empresa.
Responda sempre em português do Brasil.
Seja profissional mas amigável. Respostas curtas e diretas (máx 2-3 frases).
Não use markdown, emojis excessivos ou formatação complexa.
Se não souber algo, diga que vai encaminhar para um atendente humano.""",
        greeting="Olá! Sou o assistente virtual da empresa. Como posso ajudar?",
        fallback="Desculpe, tive uma dificuldade técnica. Um atendente humano vai entrar em contato em breve.",
        detection_keywords=["ola", "oi", "bom dia", "boa tarde", "obrigado", "obrigada", "por favor", "quero", "preciso"],
    ),
    "pt-PT": LanguageConfig(
        code="pt-PT",
        name="Português (Portugal)",
        edge_tts_voice="pt-PT-RaquelNeural",
        whisper_language="portuguese",
        system_prompt="""É um assistente virtual inteligente e prestativo de uma empresa.
Responda sempre em português de Portugal.
Seja profissional mas simpático. Respostas curtas e diretas (máx 2-3 frases).
Não use markdown, emojis excessivos ou formatação complexa.
Se não souber algo, diga que vai encaminhar para um atendente humano.""",
        greeting="Olá! Sou o assistente virtual da empresa. Como posso ajudá-lo?",
        fallback="Desculpe, tive uma dificuldade técnica. Um atendente humano irá contactá-lo em breve.",
        detection_keywords=["ola", "bom dia", "boa tarde", "obrigado", "obrigada", "por favor", "quero", "preciso"],
    ),
    "es": LanguageConfig(
        code="es",
        name="Español",
        edge_tts_voice="es-ES-ElviraNeural",
        whisper_language="spanish",
        system_prompt="""Eres un asistente virtual inteligente y servicial de una empresa.
Responde siempre en español.
Sé profesional pero cercano. Respuestas cortas y directas (máx 2-3 frases).
No uses markdown, emojis excesivos o formato complejo.
Si no sabes algo, di que lo redirigirás a un humano.""",
        greeting="¡Hola! Soy el asistente virtual de la empresa. ¿Cómo puedo ayudarte?",
        fallback="Lo siento, tuve una dificultad técnica. Un agente humano se pondrá en contacto contigo pronto.",
        detection_keywords=["hola", "buenos dias", "buenas tardes", "gracias", "por favor", "quiero", "necesito"],
    ),
    "ca": LanguageConfig(
        code="ca",
        name="Català",
        edge_tts_voice="ca-ES-JoanaNeural",
        whisper_language="catalan",
        system_prompt="""Ets un assistent virtual intel·ligent i servicial d'una empresa.
Respon sempre en català.
Sigues professional però proper. Respostes curtes i directes (màx 2-3 frases).
No utilitzis markdown, emojis excessius o format complex.
Si no saps algo, digues que ho redirigiràs a un humà.""",
        greeting="Hola! Soc l'assistent virtual de l'empresa. Com puc ajudar-te?",
        fallback="Ho sento, he tingut una dificultat tècnica. Un agent humà es posarà en contacte amb tu aviat.",
        detection_keywords=["hola", "bon dia", "bones tardes", "gràcies", "si us plau", "vull", "necessito"],
    ),
    "en": LanguageConfig(
        code="en",
        name="English",
        edge_tts_voice="en-US-JennyNeural",
        whisper_language="english",
        system_prompt="""You are an intelligent and helpful virtual assistant for a company.
Always respond in English.
Be professional but friendly. Keep responses short and direct (max 2-3 sentences).
Do not use markdown, excessive emojis, or complex formatting.
If you don't know something, say you'll route them to a human agent.""",
        greeting="Hello! I'm the company's virtual assistant. How can I help?",
        fallback="Sorry, I experienced a technical difficulty. A human agent will reach out to you shortly.",
        detection_keywords=["hello", "hi", "good morning", "good afternoon", "thanks", "please", "i want", "i need"],
    ),
}

# Whisper detection mapping
WHISPER_TO_LANG = {
    "portuguese": "pt-BR",  # Default to BR
    "spanish": "es",
    "catalan": "ca",
    "english": "en",
    "french": "fr",
    "italian": "it",
    "german": "de",
}

# Text message language detection (keyword-based)
def detect_language_from_text(text: str) -> str:
    """Choose a supported language from whole-word cues, not substrings.

    Shared greetings such as "hola" cannot identify Catalan alone.
    Stronger distinctive phrases take precedence over shared words.
    """
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))

    cues = {
        "ca": ("gracies", "si us plau", "bon dia", "bones tardes", "vull", "puc", "adeu"),
        "pt-BR": ("obrigado", "obrigada", "bom dia", "boa tarde", "por gentileza",
                  "quero", "preciso", "ola", "oi", "voce", "tudo bem"),
        "es": ("gracias", "buenos dias", "buenas tardes", "quiero",
               "necesito", "como estas", "adios"),
        "en": ("hello", "thanks", "please", "good morning",
               "good afternoon", "i want", "i need"),
    }

    def contains_phrase(phrase: str) -> bool:
        return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", normalized) is not None

    scores = {language: sum(1 for phrase in phrases if contains_phrase(phrase))
              for language, phrases in cues.items()}

    best = max(scores.values(), default=0)
    if best:
        for language in ("ca", "pt-BR", "es", "en"):
            if scores[language] == best:
                return language

    # "hola" is shared with Catalan. Without other evidence,
    # Spanish is the conservative regional fallback.
    return "es" if contains_phrase("hola") else "en"


def get_lang_config(lang_code: str) -> LanguageConfig:
    """Get language configuration by code."""
    return LANGUAGES.get(lang_code, LANGUAGES["en"])


def get_all_languages() -> list:
    """Get list of all supported languages."""
    return [{"code": k, "name": v.name} for k, v in LANGUAGES.items()]
