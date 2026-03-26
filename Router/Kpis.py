from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Kpis import Kpis
from Utils.decorator import http_decorator
from Config.db import get_db

kpis_router = APIRouter()


@kpis_router.post('/kpis/listar', tags=["KPIS"], response_model=dict)
@http_decorator
def listar_kpis(request: Request, db: Session = Depends(get_db)):
    """
    Retorna los KPIs del proceso de envío WhatsApp:
    total_envios, enviados, fallidos, efectividad (%).
    """
    data = getattr(request.state, "json_data", {})
    return Kpis(db).listar(data)
