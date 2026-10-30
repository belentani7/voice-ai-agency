"use strict";

// No analytics, cookies, storage, remote scripts or arbitrary command execution.
const $ = (selector) => document.querySelector(selector);
const labels = { teacher: "Profesora", partner: "Compañero", critic: "Revisor" };
const voices = { teacher: { pitch: 1.08, rate: 0.95 }, partner: { pitch: 1.0, rate: 1.04 }, critic: { pitch: 0.87, rate: 0.93 } };
const locale = { es: "es-ES", pt: "pt-BR", en: "en-US" };
let role = "teacher";
let busy = false;
let recognition = null;
let controller = null;
let history = [];
const maxHistory = 8;
const messageInput = $("#message");
const messages = $("#messages");
const notice = $("#notice");

function inform(text) { notice.textContent = text; }
function selectRole(next) {
  if (!Object.prototype.hasOwnProperty.call(labels, next)) return;
  role = next;
  document.querySelectorAll(".agent").forEach((el) => {
    el.setAttribute("aria-pressed", String(el.dataset.role === next));
  });
  $("#target").textContent = labels[next];
}
function appendMessage(who, text, isUser) {
  $("#empty")?.remove();
  const article = document.createElement("article");
  article.className = "message " + (isUser ? "user" : "agent-message");
  const name = document.createElement("span");
  name.className = "speaker";
  name.textContent = who;
  const body = document.createElement("p");
  body.textContent = text; // Never insert LLM content as HTML.
  article.append(name, body);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}
function speak(text, speaker) {
  if (!$("#autoSpeak").checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = locale[$("#lang").value];
  utterance.rate = voices[speaker].rate;
  utterance.pitch = voices[speaker].pitch;
  utterance.volume = Number($("#volume").value) / 100;
  const preferred = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(utterance.lang.slice(0, 2).toLowerCase()));
  if (preferred) utterance.voice = preferred;
  window.speechSynthesis.speak(utterance);
}
async function checkStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Status HTTP " + response.status);
    const status = await response.json();
    const ready = Boolean(status.available);
    $("#status").classList.toggle("ready", ready);
    $("#statusText").textContent = ready ? "Ollama local · " + status.model : "Modelo no disponible · " + status.model;
    if (!ready) inform("Instala Ollama y ejecuta: ollama pull " + status.model + ". El estudio funciona solo con tu Ollama local.");
  } catch {
    $("#status").classList.remove("ready");
    $("#statusText").textContent = "Servidor local no disponible";
  }
}
async function sendTurn() {
  if (busy) return;
  const question = messageInput.value.trim();
  if (!question) { inform("Escribe o dicta una pregunta primero."); messageInput.focus(); return; }
  if (question.length > 2500) { inform("Máximo 2500 caracteres."); return; }
  busy = true;
  inform("");
  const chosenRole = role;
  const prior = history.slice(-maxHistory);
  $("#submit").disabled = true;
  $("#submit").textContent = "Pensando…";
  controller = new AbortController();
  try {
    const response = await fetch("/api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Requested-With": "ClassroomStudio" },
      body: JSON.stringify({ role: chosenRole, question, language: $("#lang").value, history: prior }),
      signal: controller.signal
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Error de respuesta");
    appendMessage("Tú", question, true);
    appendMessage(labels[chosenRole], result.text, false);
    history = [...prior, { role: "user", content: question }, { role: "assistant", content: result.text }].slice(-maxHistory);
    messageInput.value = "";
    speak(result.text, chosenRole);
  } catch (error) {
    inform(error.name === "AbortError" ? "Consulta detenida." : (error.message || "No se pudo conectar."));
  } finally {
    busy = false;
    controller = null;
    $("#submit").disabled = false;
    $("#submit").replaceChildren(document.createTextNode("Hablar con " + labels[role] + " ↗"));
  }
}

function toggleMic() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { inform("Este navegador no ofrece dictado. Puedes escribir o usar otro navegador compatible."); return; }
  if (recognition) { recognition.stop(); return; }
  const active = new Recognition();
  recognition = active;
  active.lang = locale[$("#lang").value];
  active.interimResults = false;
  active.continuous = false;
  active.maxAlternatives = 1;
  $("#mic").setAttribute("aria-pressed", "true");
  $("#micHint").textContent = "Escuchando…";
  inform("Dictado activado. Algunos navegadores pueden procesar audio mediante servicios externos.");
  active.onresult = (event) => {
    const text = Array.from(event.results).map((part) => part[0].transcript).join(" ");
    messageInput.value = (messageInput.value + " " + text).trim().slice(0, 2500);
    messageInput.focus();
  };
  active.onerror = (event) => { inform("Micrófono: " + (event.error || "error desconocido")); };
  active.onend = () => {
    if (recognition === active) recognition = null;
    $("#mic").setAttribute("aria-pressed", "false");
    $("#micHint").textContent = "Escribe o dicta tu pregunta";
  };
  try { active.start(); } catch { active.onend(); inform("No se pudo iniciar el micrófono."); }
}
function chime() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) { inform("Audio no compatible."); return; }
  const context = new AudioContext();
  const now = context.currentTime;
  [660, 880, 1320].forEach((freq, i) => {
    const osc = context.createOscillator();
    const gain = context.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, now + i * 0.07);
    gain.gain.exponentialRampToValueAtTime(0.1, now + i * 0.07 + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.07 + 0.6);
    osc.connect(gain).connect(context.destination);
    osc.start(now + i * 0.07);
    osc.stop(now + i * 0.07 + 0.65);
  });
  window.setTimeout(() => context.close(), 1100);
}
document.querySelectorAll(".agent").forEach((el) => el.addEventListener("click", () => {
  selectRole(el.dataset.role);
  if (messageInput.value.trim()) sendTurn();
  else messageInput.focus();
}));
$("#composer").addEventListener("submit", (event) => { event.preventDefault(); sendTurn(); });
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); sendTurn(); }
});
$("#mic").addEventListener("click", toggleMic);
$("#stop").addEventListener("click", () => {
  if (recognition) recognition.stop();
  if (controller) controller.abort();
  if ("speechSynthesis" in window) speechSynthesis.cancel();
});
$("#chime").addEventListener("click", chime);
$("#volume").addEventListener("input", () => { $("#volumeValue").textContent = $("#volume").value + "%"; });
$("#clear").addEventListener("click", () => {
  history = [];
  messages.replaceChildren();
  const empty = document.createElement("div");
  empty.className = "empty";
  empty.id = "empty";
  empty.textContent = "Sesión limpia. Haz una pregunta para empezar.";
  messages.append(empty);
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  inform("Historial de esta sesión eliminado de la pantalla.");
  messageInput.focus();
});
checkStatus();
