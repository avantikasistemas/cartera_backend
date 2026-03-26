import io
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from Class.Estados import Estados
from Utils.decorator import http_decorator
from Utils.pdf_service import generar_pdf_bytes
from Config.db import get_db

estados_router = APIRouter()

PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "Uploads")


@estados_router.post('/estados/listar', tags=["ESTADOS"], response_model=dict)
@http_decorator
def listar_estados(request: Request, db: Session = Depends(get_db)):
    """Consulta cartera por rango de fechas y NIT opcional."""
    data = getattr(request.state, "json_data", {})
    return Estados(db).listar(data)


@estados_router.post('/estados/pdf', tags=["ESTADOS"], response_model=dict)
@http_decorator
def generar_pdf(request: Request, db: Session = Depends(get_db)):
    """Genera el PDF de estado de cuenta para un cliente."""
    data = getattr(request.state, "json_data", {})
    return Estados(db).generar_pdf(data)


@estados_router.post('/estados/pdf-preview', tags=["ESTADOS"])
async def preview_pdf(request: Request):
    """Genera el PDF en memoria y lo retorna como stream sin guardar en disco."""
    data = getattr(request.state, "json_data", {})
    cliente    = data.get("cliente")
    nit        = data.get("nit")
    facturas   = data.get("facturas", [])
    fecha_corte = data.get("fecha_corte")

    if not cliente or not nit:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"code": 400, "message": "cliente y nit son requeridos"})

    pdf_bytes = generar_pdf_bytes(cliente, nit, facturas, fecha_corte)
    nombre    = f"estado_cartera_{str(nit).replace('/', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nombre}"},
    )


@estados_router.post('/estados/enviar', tags=["ESTADOS"], response_model=dict)
@http_decorator
def enviar_whatsapp(request: Request, db: Session = Depends(get_db)):
    """Genera el PDF y lo envía por WhatsApp a un cliente individual."""
    data = getattr(request.state, "json_data", {})
    return Estados(db).enviar(data)


@estados_router.post('/estados/enviar-masivo', tags=["ESTADOS"], response_model=dict)
@http_decorator
def enviar_masivo(request: Request, db: Session = Depends(get_db)):
    """Envía el estado de cartera por WhatsApp a una lista de clientes."""
    data = getattr(request.state, "json_data", {})
    return Estados(db).enviar_masivo(data)


@estados_router.post('/estados/kpis', tags=["ESTADOS"], response_model=dict)
@http_decorator
def kpis(request: Request, db: Session = Depends(get_db)):
    """Retorna los KPIs de envíos WhatsApp."""
    return Estados(db).kpis()


@estados_router.post('/gestiones/crear', tags=["GESTIONES"], response_model=dict)
@http_decorator
def crear_gestion(request: Request, db: Session = Depends(get_db)):
    """Guarda una gestión de cartera con clasificación IA."""
    data = getattr(request.state, "json_data", {})
    return Estados(db).crear_gestion(data)


@estados_router.post('/gestiones/historial', tags=["GESTIONES"], response_model=dict)
@http_decorator
def historial_gestiones(request: Request, db: Session = Depends(get_db)):
    """Retorna el historial completo de gestiones de cartera para un NIT.
    Body: { "nit": "123456" }
    """
    data = getattr(request.state, "json_data", {})
    return Estados(db).listar_historial_gestiones(data)
