# Voice AI Agency

Plataforma de experimentación de agentes de voz, con foco en España, Brasil y LATAM.

> **Estado verificado (30-10-2026):** este repositorio contiene un punto de entrada FastAPI mínimo y un nuevo módulo de aula local ejecutable. No hay en esta rama una implementación funcional de WhatsApp/Instagram/Twilio, CRM, STT local ni dashboard de clientes. Esos canales son líneas futuras y no se deben presentar como desplegados.

## Producto utilizable: Aula Viva

**Tres voces en una clase**: una profesora, un compañero y un revisor. Elige agente, formula una pregunta por teclado o dictado, consulta tu Ollama local, escucha la respuesta o detén el audio. Interfaz responsive con campana Web Audio, idioma ES/PT-BR/EN y transcripción temporal.

```bash
# Instala Ollama en tu PC y descarga este modelo
ollama pull qwen2.5:7b
# Con Ollama abierto:
python -m classroom.server
# Abre http://127.0.0.1:8765
```

**Documentación, límites de privacidad y pruebas:** [classroom/README.md](classroom/README.md).

No necesitas llaves externas para el estudio. Su API solo acepta acceso desde loopback y llama a Ollama local. El dictado con Web Speech API **puede usar servidores del navegador**, así que no actives el micrófono si necesitas audio estrictamente offline. Las conversaciones no se guardan en disco.

## Entrypoint FastAPI existente

```bash
python -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Rutas presentes: `/`, `/health`, `/config` (sin secretos). Este servicio es independiente del estudio de aula, que usa `classroom.server` y se ejecuta localmente.

## Pruebas

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
node --check classroom/app.js
```

La CI de GitHub comprueba el código Python, los casos de seguridad del estudio y la sintaxis JS.

## Próximas capacidades, no implementadas

Integración STT y TTS 100 % local verificable, streaming y turnos con interrupción; después una interfaz web multiusuario con autenticación, y solo posteriormente canales empresariales/CRM. No publicar el servidor del aula directamente en Internet.

## Procedencia

Aula Viva es una transformación acotada de la **idea de aula conversacional por voz** presente en una exportación personal de conversaciones. El archivo original (522 MB) y sus datos privados permanecen fuera de este repositorio. No se han trasladado las conversaciones completas ni se han mezclado proyectos educativos o musicales.

MIT.
