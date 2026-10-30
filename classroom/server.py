"""Local-only, dependency-free classroom voice studio backend.

Run: python -m classroom.server
No chat export, microphone audio or transcripts are stored on disk.
Only the local Ollama API is contacted; browser speech recognition may use
browser-managed services and must be activated explicitly by the user.
"""
from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "qwen2.5:7b"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,79}$")
HOST = "127.0.0.1"
OLLAMA = "http://127.0.0.1:11434"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
ROLES = {
    "teacher": "Eres la profesora del aula. Explicas conceptos con precisión, ejemplos concretos y una pregunta final para comprobar comprensión.",
    "partner": "Eres un compañero de clase colaborativo. Haces conexiones útiles, ofreces un ejemplo y evitas fingir conocimientos.",
    "critic": "Eres un revisor académico constructivo. Señalas una suposición discutible y propones cómo comprobarla; nunca ridiculizas al usuario.",
}
LANGUAGES = {"es": "español", "pt": "português do Brasil", "en": "English"}


def configured_model() -> str:
    model = os.getenv("CLASSROOM_OLLAMA_MODEL", DEFAULT_MODEL).strip()
    if not MODEL_PATTERN.fullmatch(model):
        raise ValueError("CLASSROOM_OLLAMA_MODEL contains invalid characters")
    return model


def ollama_status() -> dict:
    model = configured_model()
    try:
        with urlopen(f"{OLLAMA}/api/tags", timeout=2) as response:
            payload = json.load(response)
        models = payload.get("models", [])
        installed = [item.get("name", "") for item in models if isinstance(item, dict)]
        return {"available": model in installed or any(name.split(":")[0] == model.split(":")[0] for name in installed if ":" not in model), "model": model, "installed": installed[:30]}
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return {"available": False, "model": model, "installed": []}


def validate_turn(payload: object) -> tuple[str, str, str, list[dict[str, str]]]:
    if not isinstance(payload, dict):
        raise ValueError("Se requiere un objeto JSON.")
    role = payload.get("role")
    question = payload.get("question")
    lang = payload.get("language", "es")
    history = payload.get("history", [])
    if role not in ROLES:
        raise ValueError("Agente desconocido.")
    if not isinstance(question, str) or not question.strip() or len(question) > 2500:
        raise ValueError("El mensaje debe contener entre 1 y 2500 caracteres.")
    if lang not in LANGUAGES:
        raise ValueError("Idioma desconocido.")
    if not isinstance(history, list) or len(history) > 8:
        raise ValueError("Historial no válido: máximo 8 intervenciones.")
    clean_history = []
    for item in history:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            raise ValueError("Historial no válido.")
        content = item.get("content")
        if not isinstance(content, str) or len(content) > 2500:
            raise ValueError("Historial no válido.")
        clean_history.append({"role": item["role"], "content": content})
    return role, question.strip(), lang, clean_history


def chat(role: str, question: str, lang: str, history: list[dict[str, str]]) -> str:
    messages = [
        {"role": "system", "content": ROLES[role] + " Responde solo en " + LANGUAGES[lang] + ". Limita la respuesta a unas 120 palabras. No puedes ejecutar comandos, abrir archivos ni acceder al sistema. No afirmes haberlo hecho."},
        *history,
        {"role": "user", "content": question},
    ]
    body = json.dumps({"model": configured_model(), "messages": messages, "stream": False, "options": {"temperature": 0.5, "num_predict": 250}}).encode("utf-8")
    request = Request(f"{OLLAMA}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=75) as response:
        data = json.load(response)
    content = data.get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("La respuesta del modelo está vacía.")
    return content[:5000]


class Handler(BaseHTTPRequestHandler):
    server_version = "ClassroomStudio/1.0"

    def log_message(self, format: str, *args: object) -> None:
        # Do not log transcripts, query parameters or request bodies.
        return

    def _headers(self, status: int, content_type: str, size: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()

    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        allowed_hosts = (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")
        if host not in allowed_hosts:
            return False
        return origin is None or origin in (f"http://{allowed_hosts[0]}", f"http://{allowed_hosts[1]}")

    def do_GET(self) -> None:
        if not self._same_origin():
            self._json(403, {"error": "Acceso local únicamente."})
            return
        if self.path == "/api/status":
            self._json(200, ollama_status())
            return
        asset = ASSETS.get(self.path)
        if asset is None:
            self._json(404, {"error": "No encontrado."})
            return
        filename, content_type = asset
        body = Path(__file__).with_name(filename).read_bytes()
        self._headers(200, content_type, len(body))
        self.wfile.write(body)

    def do_POST(self) -> None:
        if not self._same_origin():
            self._json(403, {"error": "Acceso local únicamente."})
            return
        if self.path != "/api/turn":
            self._json(404, {"error": "No encontrado."})
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json" or self.headers.get("X-Requested-With") != "ClassroomStudio":
            self._json(415, {"error": "Se requiere una petición JSON desde el estudio."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = -1
        if size <= 0 or size > 16000:
            self._json(413, {"error": "Petición vacía o demasiado grande."})
            return
        try:
            payload = json.loads(self.rfile.read(size))
            role, question, lang, history = validate_turn(payload)
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            self._json(422, {"error": str(exc)[:200]})
            return
        try:
            answer = chat(role, question, lang, history)
        except (HTTPError, URLError, OSError, ValueError, TimeoutError):
            self._json(503, {"error": "No se pudo consultar Ollama local. Abre Ollama y descarga el modelo configurado."})
            return
        self._json(200, {"role": role, "text": answer})


def main() -> None:
    configured_model()
    port = int(os.getenv("CLASSROOM_PORT", "8765"))
    if not 1024 <= port <= 65535:
        raise ValueError("CLASSROOM_PORT debe estar entre 1024 y 65535.")
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Classroom Studio: http://{HOST}:{port} — solo local", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
