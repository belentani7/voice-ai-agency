"""Multi-language support for Voice AI Agency Platform.

5 languages with per-language:
- Edge-TTS voice IDs
- Whisper language detection mapping
- System prompts (personality + behavior)
- Greeting messages
- Fallback messages
"""

from dataclasses import dataclass
import re
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
}

# Audio is never translated implicitly. The TTS voice and lesson locale must match.
# These are the locales for which this service currently has explicit voice IDs.
LANGUAGE_ALIASES = {
    "pt": "pt-BR", "pt-br": "pt-BR", "pt-pt": "pt-PT",
    "es": "es", "es-es": "es",
    "ca": "ca", "ca-es": "ca",
    "en": "en", "en-us": "en",
}


def resolve_supported_language(lang_code: str) -> str:
    """Return a supported locale or fail closed (never read Spanish with English TTS).

    Region requests such as es-MX, en-GB or fr-FR are deliberately rejected
    until a matching regional voice has been configured and tested.
    """
    if not isinstance(lang_code, str):
        raise ValueError("A supported BCP-47 language/locale string is required.")
    code = LANGUAGE_ALIASES.get(lang_code.strip().replace("_", "-").lower())
    if not code:
        raise ValueError(f"Unsupported voice locale: {lang_code!r}")
    return code


def detect_language_from_text(text: str, preferred_language: Optional[str] = None) -> str:
    """Use *whole word* evidence, not substring matches; honor regional preference.

    Short greetings ('hola'), shared terms ('por favor') and mixed language
    sentences are ambiguous. Keep the explicitly selected language in those cases.
    For unconstrained text, default to English only when evidence is absent.
    Never infer pt-PT versus pt-BR from shared vocabulary.
    """
    preference = resolve_supported_language(preferred_language) if preferred_language else None
    if not isinstance(text, str):
        return preference or "en"
    words = re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE)
    padded = " " + " ".join(words) + " "
    signatures = {
        "ca": ("gràcies", "si us plau", "bon dia", "bona tarda", "vull", "puc", "necessito"),
        "pt-BR": ("olá", "obrigado", "obrigada", "bom dia", "boa tarde", "quero", "preciso", "você", "vocês"),
        "es": ("gracias", "buenos días", "buenos dias", "buenas tardes", "quiero", "necesito", "puedes", "usted"),
        "en": ("hello", "thanks", "please", "good morning", "good afternoon", "i want", "i need"),
    }
    scores = {language: sum((" " + phrase + " ") in padded for phrase in phrases)
              for language, phrases in signatures.items()}
    highest = max(scores.values(), default=0)
    leaders = [language for language, score in scores.items() if score == highest and score > 0]
    if preference and (not leaders or preference in leaders or
                       (preference == "pt-PT" and "pt-BR" in leaders)):
        return preference
    if len(leaders) == 1:
        detected = leaders[0]
        if detected == "pt-BR" and preference == "pt-PT":
            return preference
        return detected
    if preference:
        return preference
    if "hola" in words and not leaders:
        return "es"  # shared with Catalan; use 'ca' when explicitly selected
    return "en"  # No confident evidence: callers should request a locale explicitly.


def get_lang_config(lang_code: str) -> LanguageConfig:
    """Return an explicitly matching TTS locale, never silently substitute English."""
    return LANGUAGES[resolve_supported_language(lang_code)]


def get_all_languages() -> list:
    """Get list of all supported languages."""
    return [{"code": k, "name": v.name} for k, v in LANGUAGES.items()]
