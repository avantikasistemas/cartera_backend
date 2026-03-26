from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Logs import Logs
from Utils.decorator import http_decorator
from Config.db import get_db

logs_router = APIRouter()


@logs_router.post('/logs/listar', tags=["LOGS"], response_model=dict)
@http_decorator
def listar_logs(request: Request, db: Session = Depends(get_db)):
    """
    Retorna el historial de envíos WhatsApp.
    Body (todos opcionales): { "limite": 200, "nit": "123456", "estado": "Enviado" }
    """
    data = getattr(request.state, "json_data", {})
    return Logs(db).listar(data)
