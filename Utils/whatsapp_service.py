import os
import requests

WHATSAPP_API_URL         = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com")
WHATSAPP_API_VERSION     = os.getenv("WHATSAPP_API_VERSION", "v23.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_TOKEN       = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PUBLIC_BASE_URL = os.getenv("WHATSAPP_PUBLIC_BASE_URL", "http://127.0.0.1:8017")
PDF_OUTPUT_DIR           = os.getenv("PDF_OUTPUT_DIR", "Uploads")


def build_public_pdf_url(filename: str) -> str:
    base = WHATSAPP_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/Uploads/{filename}"


def _subir_pdf_a_meta(filepath: str, filename: str) -> str | None:
    """Sube el PDF a Meta Media API y retorna el media_id, o None si falla."""
    upload_url = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    try:
        if not os.path.exists(filepath):
            print(f"[WhatsApp] PDF no encontrado en: {filepath}")
            return None
        with open(filepath, "rb") as f:
            r = requests.post(
                upload_url,
                headers=headers,
                files={"file": (filename, f, "application/pdf")},
                data={"messaging_product": "whatsapp", "type": "application/pdf"},
                timeout=60,
            )
        data = r.json()
        print(f"[WhatsApp] Upload media → Status: {r.status_code} | {data}")
        return data.get("id")
    except Exception as e:
        print(f"[WhatsApp] Error subiendo PDF: {e}")
        return None


def enviar_documento(numero: str, filename: str) -> dict:
    if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return {
            "ok": False,
            "status": "config_incompleta",
            "message": "Debes configurar WHATSAPP_API_TOKEN y WHATSAPP_PHONE_NUMBER_ID en .env",
        }

    url = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    public_url = build_public_pdf_url(filename)

    # ── 1. Enviar template (abre la ventana de conversación) ─────────────
    payload_template = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": "estado_cartera",
            "language": {"code": "es_CO"},
        },
    }
    try:
        r1 = requests.post(url, headers=headers, json=payload_template, timeout=40)
        data1 = r1.json() if r1.content else {}
        print(f"[WhatsApp] Template → Status: {r1.status_code} | Response: {data1}")

        if not r1.ok:
            return {"ok": False, "status_code": r1.status_code, "data": data1, "public_url": public_url}

        # ── 2. Subir PDF a Meta y obtener media_id ────────────────────────
        pdf_path = os.path.join(os.getcwd(), "Uploads", filename)
        print(f"[WhatsApp] Buscando PDF en: {pdf_path}")
        media_id = _subir_pdf_a_meta(pdf_path, filename)

        if media_id:
            # Enviar con media_id (sin URL, sin ngrok)
            payload_doc = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "document",
                "document": {
                    "id": media_id,
                    "filename": filename,
                },
            }
        else:
            # Fallback: enviar por URL pública
            payload_doc = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "document",
                "document": {
                    "link": public_url,
                    "filename": filename,
                },
            }

        r2 = requests.post(url, headers=headers, json=payload_doc, timeout=40)
        data2 = r2.json() if r2.content else {}
        print(f"[WhatsApp] Documento → Status: {r2.status_code} | Response: {data2}")

        return {
            "ok": r2.ok,
            "status_code": r2.status_code,
            "data": data2,
            "public_url": public_url,
        }
    except requests.RequestException as e:
        return {"ok": False, "status": "error_red", "message": str(e)}
