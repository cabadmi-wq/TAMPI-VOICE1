import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

TZ = ZoneInfo(os.getenv("TIMEZONE", "America/Guayaquil"))
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "TAMPI VOICE Demo")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE", "")
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Google Calendar is optional for the first voice test.
# To enable it, set GOOGLE_SERVICE_ACCOUNT_JSON to the contents of a
# service-account JSON file and share the target Google Calendar with
# that service-account email.
def get_calendar_service():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def parse_dt(value: str):
    """Accept ISO-8601 date/time; assume Ecuador time if no timezone."""
    if not value:
        raise ValueError("Falta fecha/hora.")
    value = value.strip()
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def check_availability(start_dt, duration_minutes=60):
    service = get_calendar_service()
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    if service is None:
        # Demo mode: no Google Calendar configured.
        return {
            "available": True,
            "demo_mode": True,
            "message": "Disponibilidad simulada: configura Google Calendar para usar disponibilidad real."
        }

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "items": [{"id": CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    busy = result.get("calendars", {}).get(CALENDAR_ID, {}).get("busy", [])
    return {
        "available": len(busy) == 0,
        "demo_mode": False,
        "busy": busy,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
    }


def book_appointment(start_dt, duration_minutes, customer_name, customer_phone, service_name, notes=""):
    service = get_calendar_service()
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    availability = check_availability(start_dt, duration_minutes)
    if not availability["available"]:
        return {
            "status": "not_available",
            "message": "Ese horario ya no está disponible. Consulta otro horario."
        }

    if service is None:
        return {
            "status": "demo_booked",
            "demo_mode": True,
            "message": "Reserva simulada creada. Configura Google Calendar para crear eventos reales.",
            "date": start_dt.strftime("%Y-%m-%d"),
            "time": start_dt.strftime("%H:%M"),
        }

    event = {
        "summary": f"{service_name or 'Cita'} - {customer_name}",
        "description": (
            f"Cliente: {customer_name}\n"
            f"Teléfono: {customer_phone}\n"
            f"Servicio: {service_name}\n"
            f"Notas: {notes}"
        ),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": str(TZ),
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": str(TZ),
        },
    }

    created = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event,
    ).execute()

    return {
        "status": "booked",
        "demo_mode": False,
        "event_id": created.get("id"),
        "date": start_dt.strftime("%Y-%m-%d"),
        "time": start_dt.strftime("%H:%M"),
        "message": "Cita creada correctamente.",
    }


def handle_tool(name, args):
    args = args or {}

    if name == "business_info":
        return {
            "business_name": BUSINESS_NAME,
            "phone": BUSINESS_PHONE,
            "address": BUSINESS_ADDRESS,
            "timezone": str(TZ),
            "message": "Información básica del negocio."
        }

    if name == "check_availability":
        start = parse_dt(args.get("start"))
        duration = int(args.get("duration_minutes", 60))
        return check_availability(start, duration)

    if name == "book_appointment":
        start = parse_dt(args.get("start"))
        duration = int(args.get("duration_minutes", 60))
        return book_appointment(
            start_dt=start,
            duration_minutes=duration,
            customer_name=args.get("customer_name", ""),
            customer_phone=args.get("customer_phone", ""),
            service_name=args.get("service_name", ""),
            notes=args.get("notes", ""),
        )

    return {"error": f"Herramienta desconocida: {name}"}


@app.get("/")
def index():
    return render_template(
        "index.html",
        business_name=BUSINESS_NAME,
        calendar_enabled=bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
    )


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "TAMPI VOICE MVP",
        "calendar_configured": bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
        "timezone": str(TZ),
    })


@app.post("/webhook/vapi")
def vapi_webhook():
    """
    Vapi sends:
      { "message": { "type": "tool-calls", "toolCallList": [...] } }

    We return:
      { "results": [{ "toolCallId": "...", "result": "..." }] }

    Always return HTTP 200, including tool errors.
    """
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", {})
    msg_type = message.get("type")

    if msg_type != "tool-calls":
        return jsonify({"received": True})

    results = []
    for call in message.get("toolCallList", []):
        tool_id = call.get("id")
        function = call.get("function", {})
        name = function.get("name")
        args = function.get("arguments", {})

        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = handle_tool(name, args)
            results.append({
                "toolCallId": tool_id,
                "result": json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            })
        except Exception as exc:
            results.append({
                "toolCallId": tool_id,
                "error": str(exc).replace("\n", " ")
            })

    return jsonify({"results": results})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
