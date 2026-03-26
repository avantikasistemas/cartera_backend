import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CATEGORIES = [
    "confirmo_pago",
    "promesa_pago",
    "solicita_reenvio",
    "reporta_diferencia",
    "sin_respuesta_util",
]


def clasificar_respuesta(texto: str) -> dict:
    texto = (texto or "").strip()
    if not texto:
        return {"tipo": "sin_respuesta_util", "fuente": "regla_local"}

    # Clasificación local si no hay clave Gemini configurada
    if not GEMINI_API_KEY:
        lower = texto.lower()
        if any(w in lower for w in ["confirm", "pag", "cancel"]):
            return {"tipo": "confirmo_pago", "fuente": "regla_local"}
        if any(w in lower for w in ["viernes", "lunes", "semana", "promesa", "próximo"]):
            return {"tipo": "promesa_pago", "fuente": "regla_local"}
        if "reenv" in lower:
            return {"tipo": "solicita_reenvio", "fuente": "regla_local"}
        if "diferencia" in lower:
            return {"tipo": "reporta_diferencia", "fuente": "regla_local"}
        return {"tipo": "sin_respuesta_util", "fuente": "regla_local"}

    prompt = (
        f"Clasifica la siguiente respuesta de un cliente de cartera en una sola categoría JSON.\n"
        f"Categorías disponibles: {', '.join(CATEGORIES)}\n"
        f"Texto: {texto}\n\n"
        f"Responde exclusivamente JSON: {{\"tipo\":\"categoria\"}}"
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    try:
        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        text_out = data["candidates"][0]["content"]["parts"][0]["text"]
        for item in CATEGORIES:
            if item in text_out:
                return {"tipo": item, "fuente": GEMINI_MODEL}
    except Exception:
        pass

    return {"tipo": "sin_respuesta_util", "fuente": "regla_local"}
