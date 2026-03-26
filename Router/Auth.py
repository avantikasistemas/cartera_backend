from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Auth import Auth
from Utils.decorator import http_decorator
from Config.db import get_db

auth_router = APIRouter()


@auth_router.post('/login', tags=["AUTH"], response_model=dict)
@http_decorator
def login(request: Request, db: Session = Depends(get_db)):
    """Autentica un usuario con email/password y retorna un JWT."""
    data     = getattr(request.state, "json_data", {})
    response = Auth(db).login(data)
    return response
