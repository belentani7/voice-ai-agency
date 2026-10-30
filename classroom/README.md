# Aula Viva — estudio de voz local

Módulo funcional del repositorio **voice-ai-agency**, extraído como idea de producto de una conversación del historial personal del 30 de octubre de 2026. **No** incorpora al repositorio el archivo JSON original, transcripciones ni datos privados. No sustituye a las plataformas educativas ni modifica sus repositorios.

## Ejecutar

Requiere Python 3.10+ y [Ollama](https://ollama.com/). Para usar el estudio sin API externa:

```bash
ollama pull qwen2.5:7b
ollama serve                 # solo si Ollama no está iniciado
# en otra terminal y desde la raíz del repositorio:
python -m classroom.server
```

Abre **http://127.0.0.1:8765/**. No se instala ninguna dependencia de Python para el estudio. Opcionalmente:

```bash
CLASSROOM_OLLAMA_MODEL=llama3.1:8b CLASSROOM_PORT=8766 python -m classroom.server
```

Para Windows PowerShell, cambia las variables de entorno con `$env:CLASSROOM_OLLAMA_MODEL="llama3.1:8b"` y ejecuta `python -m classroom.server`. No uses un proxy público ni expongas Ollama en Internet.

## Qué funciona ahora

- Tres roles seleccionables: **Profesora**, **Compañero**, **Revisor**. Cada uno añade instrucciones contextualizadas al modelo local instalado.
- Pregunta por teclado o dictado de voz voluntario del navegador; ninguna grabación comienza sola.
- Respuesta del modelo local a través de `127.0.0.1:11434`. Si no está instalado, se informa del error: **no se simula una respuesta de IA**.
- Lectura de voz mediante `speechSynthesis` del navegador, con volumen y voz/rítmica por rol cuando la plataforma lo permita. Botón de detener.
- Campana original sintetizada con Web Audio, sin descargar sonidos externos.
- Idiomas español, portugués de Brasil e inglés.
- Historial temporal en memoria del navegador (ocho intervenciones de contexto), que se limpia al pulsar «Limpiar sesión» o cerrar la página.

## Límites reales

- **Privacidad**: el servidor se escucha solo en loopback, no registra ni persiste prompts; el backend solo se conecta al Ollama de loopback. Sin embargo, **Web Speech API** puede enviar audio a servicios administrados por el navegador, y las voces TTS pueden depender del sistema. Si necesitas procesamiento de audio estrictamente offline, **no actives el micrófono** hasta conectar un backend local de STT verificado (por ejemplo whisper.cpp o Vosk); puedes escribir normalmente.
- El estudio **no** ejecuta comandos del sistema, no busca archivos privados, no integra WhatsApp, Twilio ni CRM y no es una plataforma de llamadas.
- El estudio está hecho para una sola persona en su PC, no es un servicio multiusuario. La interfaz usa estándares web; los motores de voz varían por navegador.
- Este módulo no es aún una función del despliegue Vercel de `main.py`: se ejecuta como proceso local independiente. No deben desplegarse sus endpoints a Internet sin autenticación y otra revisión de seguridad.

## Seguridad y pruebas

- Dirección fija `127.0.0.1`, comprobación de host/origen y cabecera anti-CSRF.
- Validación estricta de roles, idioma, tamaño y estructura del historial.
- Sin interpretación de las respuestas como HTML ni comandos; no se ejecutan herramientas.
- Política CSP, no cookies, sin analytics y sin almacenamiento persistente.
- No subir nunca el JSON de exportación ni archivos `.env` al repositorio.

Ejecuta:

```bash
python -m compileall -q classroom
python -m unittest discover -s tests -v
node --check classroom/app.js
```

## Origen y destino de la función

Conservamos solo el requisito funcional del material: *una clase por voz con varios agentes y una interfaz de tarjetas y audio*. Esta implementación pertenece a `voice-ai-agency`. La adaptación futura a `open-school` o a `linguaforge` requiere contratos y validaciones específicos de esos productos; no se han realizado cambios allí.
