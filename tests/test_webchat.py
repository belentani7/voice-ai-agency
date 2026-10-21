"""Unit tests for the real Web Chat API without external LLM calls."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app, _usage
from languages import detect_language_from_text


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "Hola, ¿en qué puedo ayudar?"}}]}


class FakeAsyncClient:
    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, endpoint, headers, json):
        assert endpoint.startswith("https://api.groq.com/")
        assert headers["Authorization"] == "Bearer test-provider-key"
        assert json["messages"][0]["role"] == "system"
        return FakeResponse()


class WebChatTests(unittest.TestCase):
    def setUp(self):
        _usage.clear()
        self.client = TestClient(app)
        self.payload = {"messages": [{"role": "user", "content": "Hola"}]}

    def test_health_and_languages(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        languages = self.client.get("/api/languages").json()
        self.assertEqual({item["code"] for item in languages},
                         {"en", "es", "ca", "pt-BR", "pt-PT"})

    def test_disabled_without_server_token(self):
        with patch.dict(os.environ, {}, clear=True):
            res = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(res.status_code, 503)

    def test_bad_token_rejected(self):
        with patch.dict(os.environ, {"VOICE_AGENCY_API_TOKEN": "some-real-secret"}, clear=True):
            res = self.client.post("/api/chat", json=self.payload,
                                   headers={"Authorization": "Bearer wrong"})
        self.assertEqual(res.status_code, 401)

    def test_real_provider_protocol_with_stubbed_network(self):
        env = {"VOICE_AGENCY_API_TOKEN": "local-test-token",
               "GROQ_API_KEY": "test-provider-key",
               "LLM_PROVIDER": "groq"}
        with patch.dict(os.environ, env, clear=True), patch("main.httpx.AsyncClient", FakeAsyncClient):
            res = self.client.post("/api/chat", json=self.payload,
                                   headers={"Authorization": "Bearer local-test-token"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["language"], "es")
        self.assertIn("Hola", res.json()["reply"])

    def test_rejects_assistant_as_last_message(self):
        payload = {"messages": [{"role": "assistant", "content": "Hello"}]}
        with patch.dict(os.environ, {"VOICE_AGENCY_API_TOKEN": "test"}, clear=True):
            res = self.client.post("/api/chat", json=payload,
                                   headers={"Authorization": "Bearer test"})
        self.assertEqual(res.status_code, 422)

    def test_language_hints_do_not_match_substrings(self):
        self.assertEqual(detect_language_from_text("Hola"), "es")
        self.assertEqual(detect_language_from_text("bon dia"), "ca")
        self.assertEqual(detect_language_from_text("Olá, obrigado!"), "pt-BR")
        self.assertEqual(detect_language_from_text("Hello!"), "en")
        self.assertEqual(detect_language_from_text("holala"), "en")
        self.assertEqual(detect_language_from_text("por favor"), "es")


if __name__ == "__main__":
    unittest.main()
