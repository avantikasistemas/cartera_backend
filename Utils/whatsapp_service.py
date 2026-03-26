import os
import requests

WHATSAPP_API_URL       = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com")
WHATSAPP_API_VERSION   = os.getenv("WHATSAPP_API_VERSION", "v23.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_TOKEN     = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PUBLIC_BASE_URL = os.getenv("WHATSAPP_PUBLIC_BASE_URL", "http://127.0.0.1:8017")
PDF_OUTPUT_DIR         = os.getenv("PDF_OUTPUT_DIR", "storage/pdfs")


def build_public_pdf_url(filename: str) -> str:
    base = WHATSAPP_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/storage/pdfs/{filename}"


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
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "document",
        "document": {
            "link": public_url,
            "filename": filename,
            "caption": (
                "Hola, compartimos su estado de cartera. "
                "Agradecemos validar la información y confirmar fecha de pago. "
                "Avantika Colombia S.A.S."
            ),
        },
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}
        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "data": data,
            "public_url": public_url,
        }
    except requests.RequestException as e:
        return {"ok": False, "status": "error_red", "message": str(e)}
