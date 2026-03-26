from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Contactos import Contactos
from Utils.decorator import http_decorator
from Config.db import get_db

contactos_router = APIRouter()


@contactos_router.post("/contactos/listar", tags=["CONTACTOS"], response_model=dict)
@http_decorator
def listar_contactos(request: Request, db: Session = Depends(get_db)):
    """
    Busca contactos en CRM_contactos.
    Body (opcional): { "nit": "123456" }
    Si no se envía nit, retorna los últimos 100 contactos.
    """
    data = getattr(request.state, "json_data", {})
    return Contactos(db).listar(data)


@contactos_router.post("/contactos/crear", tags=["CONTACTOS"], response_model=dict)
@http_decorator
def crear_contacto(request: Request, db: Session = Depends(get_db)):
    """
    Crea o actualiza un contacto WhatsApp en CRM_contactos.
    Body: { "nit": "123456", "tel_celular": "3001234567", "nombre": "Whatsapp" }
    """
    data = getattr(request.state, "json_data", {})
    return Contactos(db).crear(data)
