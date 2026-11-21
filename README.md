# TAMPI VOICE — MVP 1.0

Primera versión de una recepcionista telefónica con IA.

## Qué hace

- Backend Flask preparado para Render.
- Webhook compatible con Vapi Function Tools.
- Herramienta de información del negocio.
- Consulta de disponibilidad en Google Calendar.
- Creación de citas en Google Calendar.
- Zona horaria por defecto: America/Guayaquil.
- Modo DEMO si todavía no se configura Google Calendar.

## COSTO PARA EMPEZAR

Puedes probar el concepto sin pagar infraestructura de voz al principio usando los créditos gratuitos de Vapi y su número gratuito de prueba (solo llamadas entrantes y número de EE. UU.).

Para producción en Ecuador necesitarás un proveedor de telefonía/número compatible y pagar el uso de llamadas/modelos según el proveedor elegido.

## 1. Subir a GitHub

Crea un repositorio nuevo, por ejemplo:

tampi-voice

Sube TODOS los archivos manteniendo esta estructura:

app.py
requirements.txt
render.yaml
.env.example
vapi_tools.json
README.md
templates/index.html
static/style.css

## 2. Desplegar en Render

Crea un Web Service desde el repositorio.

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

Variables:

TIMEZONE=America/Guayaquil
BUSINESS_NAME=Tu negocio
BUSINESS_PHONE=...
BUSINESS_ADDRESS=...
GOOGLE_CALENDAR_ID=primary

GOOGLE_SERVICE_ACCOUNT_JSON=
(se configura después)

## 3. Probar

Abre:

https://TU-SERVICIO.onrender.com/health

Debe aparecer:

{"ok":true,...}

## 4. Crear el agente en Vapi

Crea un Assistant/Voice Agent.

Recomendación inicial de comportamiento:

"Soy la recepcionista virtual de [NEGOCIO].
Respondo en español ecuatoriano, con tono amable y profesional.
Nunca inventes disponibilidad.
Antes de reservar confirma servicio, fecha, hora, nombre y teléfono.
Primero consulta disponibilidad.
Solo después de que el cliente confirme la cita ejecuta book_appointment.
Si una hora no está disponible, ofrece alternativas.
Si el cliente pide una persona, deriva la llamada."

Agrega las tres Function Tools del archivo vapi_tools.json.

Cambia:

https://TU-SERVICIO.onrender.com/webhook/vapi

por la URL real de Render.

## 5. Google Calendar

Para activar citas reales:

1. En Google Cloud crea un proyecto.
2. Activa Google Calendar API.
3. Crea una cuenta de servicio.
4. Descarga su JSON.
5. Comparte el calendario del negocio con el correo de la cuenta de servicio con permiso para gestionar eventos.
6. Copia el contenido JSON en la variable de Render:
   GOOGLE_SERVICE_ACCOUNT_JSON
7. Pon GOOGLE_CALENDAR_ID con el ID del calendario.

No subas el JSON de credenciales a GitHub.

## 6. Primera prueba

Primero prueba desde el botón de llamada web de Vapi.

Luego usa un número telefónico de prueba.

Conversación esperada:

Cliente:
"Hola, quiero una cita mañana a las cuatro."

IA:
"Claro. ¿Qué servicio desea?"

Cliente:
"Consulta."

IA:
"Perfecto. ¿Me indica su nombre y número?"

...

IA consulta check_availability.

Si está libre:

"Sí, tengo disponible mañana a las cuatro. ¿Desea que la reserve?"

Cliente:
"Sí."

IA ejecuta book_appointment.

## Próxima versión

La V2 de TAMPI VOICE debería agregar:

- Panel multiempresa.
- Usuarios y clientes.
- Configuración por negocio.
- Varios calendarios/profesionales.
- Horarios comerciales.
- Duración por servicio.
- Transferencia a humano.
- Historial de llamadas.
- Resúmenes automáticos.
- WhatsApp.
- SMS.
- Recordatorios.
- CRM.
- Facturación mensual.
- Control de minutos.
- Número telefónico de Ecuador.
