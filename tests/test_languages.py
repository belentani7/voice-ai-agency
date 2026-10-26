"""Regression tests for multilingual voice routing (stdlib only)."""
import unittest

from languages import (
    LANGUAGES, WHISPER_TO_LANG, detect_language_from_text,
    get_lang_config, resolve_supported_language,
)


class VoiceLocaleTests(unittest.TestCase):
    def test_supported_regional_locales(self):
        for raw, expected in {
            "PT_br": "pt-BR", "pt-PT": "pt-PT", "pt": "pt-BR",
            "es-ES": "es", "ca-ES": "ca", "en-US": "en"
        }.items():
            with self.subTest(raw=raw):
                self.assertEqual(resolve_supported_language(raw), expected)
                self.assertEqual(get_lang_config(raw).code, expected)

    def test_unsupported_accents_never_silently_use_english(self):
        for raw in ("fr", "es-MX", "en-GB", "pt-AO", "", None):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    get_lang_config(raw)

    def test_no_substring_false_positives(self):
        self.assertEqual(detect_language_from_text("holanda"), "en")
        self.assertEqual(detect_language_from_text("colaborar"), "en")
        self.assertEqual(detect_language_from_text("¡Hola, gracias!"), "es")
        self.assertEqual(detect_language_from_text("olá, obrigado"), "pt-BR")
        self.assertEqual(detect_language_from_text("si us plau, gràcies"), "ca")
        self.assertEqual(detect_language_from_text("please help"), "en")

    def test_explicit_locale_wins_on_ambiguous_greeting(self):
        self.assertEqual(detect_language_from_text("hola"), "es")
        self.assertEqual(detect_language_from_text("hola", "ca-ES"), "ca")
        self.assertEqual(detect_language_from_text("por favor", "pt-PT"), "pt-PT")
        self.assertEqual(detect_language_from_text("Bom dia", "pt-PT"), "pt-PT")
        self.assertEqual(detect_language_from_text("", "es-ES"), "es")
        self.assertEqual(detect_language_from_text(None, "pt-BR"), "pt-BR")

    def test_voices_and_stt_mapping_are_consistent(self):
        for lang in WHISPER_TO_LANG.values():
            self.assertIn(lang, LANGUAGES)
        for config in LANGUAGES.values():
            prefix = {"es": "es-ES", "ca": "ca-ES", "en": "en-US"}.get(config.code, config.code)
            self.assertTrue(config.edge_tts_voice.startswith(prefix + "-"))


if __name__ == "__main__":
    unittest.main()
