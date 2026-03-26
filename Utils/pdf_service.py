import io
import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "Uploads")

LOGO_PATH = Path(__file__).resolve().parent.parent / "Templates" / "logotipo.png"


def _fmt_date(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d-%b-%Y")
    return str(value)


def _dibujar_pdf(c: canvas.Canvas, cliente: str, nit: str, facturas: list, fecha_corte=None):
    """Dibuja el contenido del PDF sobre el canvas dado."""
    width, height = letter

    # ── Logo esquina superior derecha ─────────────────────────────────────────
    LOGO_W, LOGO_H = 150, 60
    logo_x = width - LOGO_W - 30          # 30pt de margen derecho
    logo_y = height - LOGO_H - 15         # 15pt de margen superior
    if LOGO_PATH.exists():
        try:
            c.drawImage(
                str(LOGO_PATH), logo_x, logo_y,
                width=LOGO_W, height=LOGO_H,
                preserveAspectRatio=True, anchor="ne", mask="auto"
            )
        except Exception:
            pass  # Si falla por cualquier razón, continua sin logo

    # ── Encabezado ────────────────────────────────────────────────────────────
    y = height - 60
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "ESTADO DE CUENTA")
    y -= 35

    c.setFont("Helvetica-Bold", 10)
    c.rect(40, y - 30, width - 80, 50)
    c.drawString(50, y, f"CLIENTE: {cliente}")
    c.drawString(50, y - 20, f"FECHA DE CORTE: {_fmt_date(fecha_corte)}")
    y -= 55

    c.rect(40, y - 25, width - 80, 35)
    c.setFont("Helvetica", 10)
    c.drawString(50, y - 5, "Estimado cliente, solicitamos por favor informar fecha de pago para las siguientes facturas.")
    y -= 45

    headers = ["TIPO", "NUMERO", "FECHA", "VENCIMIENTO", "SALDO"]
    xs = [40, 100, 200, 300, 430]
    c.setFont("Helvetica-Bold", 9)
    c.rect(40, y - 18, width - 80, 22)
    for idx, h in enumerate(headers):
        c.drawString(xs[idx] + 5, y - 5, h)
    y -= 25

    total = 0
    c.setFont("Helvetica", 9)
    for f in facturas:
        if y < 180:
            c.showPage()
            y = height - 60
        c.rect(40, y - 18, width - 80, 22)
        vals = [
            str(f.get("tipo", "")),
            str(f.get("numero", "")),
            _fmt_date(f.get("fecha")),
            _fmt_date(f.get("vencimiento")),
            f"${float(f.get('saldo', 0)):,.0f}",
        ]
        for idx, v in enumerate(vals):
            c.drawString(xs[idx] + 5, y - 5, v)
        total += float(f.get("saldo", 0))
        y -= 22

    y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 40, y, f"TOTAL FACTURAS: ${total:,.0f}")
    y -= 35

    c.setFont("Helvetica", 9)
    c.drawString(40, y, "Bancolombia Cuenta Corriente: 08010197700")
    y -= 14
    c.drawString(40, y, "Banco de Bogotá Cuenta Corriente: 170123715")
    y -= 14
    c.drawString(40, y, "Banco Davivienda Cuenta Corriente: 026169996274")
    y -= 24
    c.drawString(40, y, "Celular y WhatsApp: +57 300-8150157")
    y -= 14
    c.drawString(40, y, "Teléfono: 605-3855505 ext. 5118")
    y -= 14
    c.drawString(40, y, "E-mail: cartera@avantika.com.co")
    y -= 24
    c.drawString(40, y, "Favor realizar sus pagos mediante transferencia electrónica e informar el soporte al área de cartera.")


def generar_pdf_bytes(cliente: str, nit: str, facturas: list, fecha_corte=None) -> bytes:
    """Genera el PDF en memoria y retorna los bytes sin guardar en disco."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    _dibujar_pdf(c, cliente, nit, facturas, fecha_corte)
    c.save()
    buffer.seek(0)
    return buffer.read()


def generar_pdf(cliente: str, nit: str, facturas: list, fecha_corte=None) -> dict:
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    filename = f"estado_cartera_{str(nit).replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(PDF_OUTPUT_DIR, filename)

    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 60

    _dibujar_pdf(c, cliente, nit, facturas, fecha_corte)
    c.save()

    return {"filename": filename, "path": path}
