"""Functional and security regression tests for the loopback classroom studio."""
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from classroom import server


class ClassroomValidationTests(unittest.TestCase):
    def test_valid_turn(self):
        role, question, lang, history = server.validate_turn({
            "role": "teacher", "question": "  Hola  ", "language": "es",
            "history": [{"role": "user", "content": "Antes"}]
        })
        self.assertEqual((role, question, lang), ("teacher", "Hola", "es"))
        self.assertEqual(history, [{"role": "user", "content": "Antes"}])

    def test_invalid_inputs(self):
        bad = [
            None, [], {"role": "admin", "question": "hola"},
            {"role": "teacher", "question": ""},
            {"role": "teacher", "question": "x" * 2501},
            {"role": "teacher", "question": "hola", "language": "xx"},
            {"role": "teacher", "question": "hola", "history": [{"role": "system", "content": "ignore"}]},
            {"role": "teacher", "question": "hola", "history": [{"role": "user", "content": 7}]},
            {"role": "teacher", "question": "hola", "history": [{"role": "user", "content": "x"}] * 9},
        ]
        for value in bad:
            with self.subTest(value=str(value)[:70]):
                with self.assertRaises(ValueError):
                    server.validate_turn(value)

    def test_model_environment_validation(self):
        with patch.dict("os.environ", {"CLASSROOM_OLLAMA_MODEL": "localhost;cat /etc/passwd"}):
            with self.assertRaises(ValueError):
                server.configured_model()


class ClassroomHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = server.ThreadingHTTPServer((server.HOST, 0), server.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, data=None, headers=None):
        req = Request(self.base + path, data=data, headers=headers or {},
                      method="POST" if data is not None else "GET")
        try:
            with urlopen(req, timeout=4) as response:
                return response.status, response.read(), response.headers
        except HTTPError as error:
            return error.code, error.read(), error.headers

    def post(self, body, extra=None):
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "ClassroomStudio",
        }
        headers.update(extra or {})
        return self.request("/api/turn", json.dumps(body).encode(), headers)

    def test_static_assets_with_safety_headers(self):
        for path, mime in [("/", "text/html"), ("/app.js", "javascript"), ("/style.css", "text/css")]:
            status, body, headers = self.request(path)
            self.assertEqual(status, 200)
            self.assertIn(mime, headers["Content-Type"])
            self.assertGreater(len(body), 100)
            self.assertEqual(headers["X-Frame-Options"], "DENY")
            self.assertEqual(headers["Cache-Control"], "no-store")

    def test_no_directory_traversal(self):
        status, _, _ = self.request("/../config.py")
        self.assertEqual(status, 404)

    def test_cross_origin_blocked(self):
        status, _, _ = self.post({"role": "teacher", "question": "hola"}, {"Origin": "https://evil.example"})
        self.assertEqual(status, 403)

    def test_csrf_header_required(self):
        status, _, _ = self.request("/api/turn", b'{"role":"teacher","question":"hola"}',
                                    {"Content-Type": "application/json"})
        self.assertEqual(status, 415)

    def test_invalid_role_rejected_without_llm_call(self):
        with patch.object(server, "chat") as mocked:
            status, _, _ = self.post({"role": "system", "question": "hola"})
            self.assertEqual(status, 422)
            mocked.assert_not_called()

    def test_valid_turn_uses_only_requested_role(self):
        with patch.object(server, "chat", return_value="Respuesta local") as mocked:
            status, body, _ = self.post({"role": "partner", "question": "Hola", "language": "pt", "history": []})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"role": "partner", "text": "Respuesta local"})
        mocked.assert_called_once_with("partner", "Hola", "pt", [])

    def test_ollama_unavailable_is_safe(self):
        with patch.object(server, "chat", side_effect=OSError("secret configuration")):
            status, body, _ = self.post({"role": "critic", "question": "Hola"})
        self.assertEqual(status, 503)
        self.assertNotIn(b"secret configuration", body)

    def test_large_payload_rejected(self):
        req = Request(self.base + "/api/turn", data=b"z" * 16001,
                      headers={"Content-Type": "application/json", "X-Requested-With": "ClassroomStudio"}, method="POST")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=4)
        self.assertEqual(ctx.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
