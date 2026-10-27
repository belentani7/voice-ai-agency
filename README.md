# Voice AI Agency — Web Chat operativo

**Estado:** canal Web Chat funcional sobre proveedores de lenguaje reales, con consola administrativa local y soporte de cinco idiomas. El repositorio todavía **no** implementa captura/reconocimiento de audio, síntesis de voz, WhatsApp, Instagram, Twilio, CRM o una plataforma comercial multi-tenant. No hay simulaciones de estos canales.

## Qué funciona

- FastAPI con `GET /health`, `GET /api/languages`, `POST /api/chat` y consola web en `/`.
- Respuestas de modelos reales por Groq, OpenAI o DeepSeek mediante API HTTPS y credenciales propias.
- Español, catalán, inglés y portugués brasileño/europeo, con detección aproximada por texto.
- Hasta 12 mensajes por petición, 4.000 caracteres por mensaje y 16.000 caracteres en total; se rechazan mensajes vacíos o compuestos solo de espacios antes de contactar al proveedor.
- Token de acceso exigido por el servidor: servicio deshabilitado si no está configurado.
- Límite en memoria de 20 peticiones/minuto por IP; no sustituye un limitador compartido en despliegues con varios workers.
- No se guardan mensajes en disco ni en una base de datos. El navegador mantiene el contexto en memoria hasta cerrar/refrescar.
- Consola responsive con interacción real, navegación accesible y texto remoto renderizado como texto seguro.

## Ponerlo en marcha

Python 3.10 o posterior.

```sh
python -m venv .venv
# Activa tu entorno virtual
python -m pip install -r requirements.txt
```

Configura en el entorno (no copies claves reales al repositorio):

```sh
export VOICE_AGENCY_API_TOKEN="un-token-aleatorio-largo"
export LLM_PROVIDER="groq"
export GROQ_API_KEY="tu-clave"
python main.py
```

Para OpenAI configura `LLM_PROVIDER=openai` y `OPENAI_API_KEY`. Para DeepSeek: `LLM_PROVIDER=deepseek` y `DEEPSEEK_API_KEY`. El modelo se puede cambiar mediante `LLM_MODEL`; se usan valores por defecto por proveedor.

Abre http://127.0.0.1:8000/ e introduce el token del servidor. La consola no inserta la clave del proveedor en JavaScript. No hay llamadas externas hasta enviar mensajes autenticados.

En Windows PowerShell utiliza `$env:VOICE_AGENCY_API_TOKEN="..."`, etc.

## Pruebas

```sh
python -m compileall -q main.py config.py languages.py tests
python -m unittest discover -s tests -p 'test_*.py'
```

El test de respuestas reemplaza solo la conexión externa y verifica estructura/autenticación. Para una verificación real configura una credencial y ejecuta una conversación desde la consola.

## Seguridad, límites y siguientes integraciones

El canal recibe y envía texto al proveedor LLM elegido; verifica su política de tratamiento de datos antes de introducir información. No uses credenciales, datos bancarios, sanitarios o identificaciones reales. El servidor deshabilita la API si falta autenticación y limita el tamaño del contenido y la frecuencia, pero requiere TLS, aislamiento por cliente, gestión central de claves y auditoría antes de abrirlo a múltiples empresas.

Los canales de mensajería, llamadas, STT/TTS y panel multiempresa siguen pendientes: no los consideres publicados ni operativos. La consola es una implementación real del canal web, no una simulación de telefonía.
