"""Language detection regression tests for overlapping regional greetings."""

import unittest

from languages import detect_language_from_text, get_lang_config


class LanguageDetectionTests(unittest.TestCase):
    def test_spanish_hola_does_not_select_catalan(self):
        self.assertEqual(detect_language_from_text("Hola, ¿cómo estás?"), "es")

    def test_catalan_distinctive_phrase_wins(self):
        self.assertEqual(detect_language_from_text("Hola, moltes gràcies!"), "ca")

    def test_portuguese_ola_is_whole_word(self):
        self.assertEqual(detect_language_from_text("Olá, preciso de ajuda."), "pt-BR")

    def test_english_hello(self):
        self.assertEqual(detect_language_from_text("Hello, I need help"), "en")

    def test_ola_inside_spanish_word_not_a_portuguese_match(self):
        self.assertEqual(detect_language_from_text("Hola, colaboración y gracias"), "es")

    def test_unknown_defaults_to_supported_english(self):
        self.assertEqual(detect_language_from_text(""), "en")

    def test_detected_codes_have_configs(self):
        for sample in ("Olá", "Hola", "Gràcies", "Hello"):
            self.assertEqual(get_lang_config(detect_language_from_text(sample)).code,
                             detect_language_from_text(sample))


if __name__ == "__main__":
    unittest.main()
