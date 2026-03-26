from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from Config.db import BASE, engine
from Middleware.get_json import JSONMiddleware
from Router.Auth import auth_router
from Router.Estados import estados_router
from Router.Contactos import contactos_router
from Router.Logs import logs_router
from Router.Kpis import kpis_router
from pathlib import Path
import os

route = Path.cwd()
app = FastAPI()
app.title = "Avántika Cartera WhatsApp"
app.version = "0.0.1"

# Servir PDFs generados como archivos estáticos
app.mount("/Uploads", StaticFiles(directory=f"{route}/Uploads"), name="Uploads")

app.add_middleware(JSONMiddleware)
app.add_middleware(
    CORSMiddleware,allow_origins=["*"],  # Permitir todos los orígenes; para producción, especifica los orígenes permitidos.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos; puedes especificar los métodos permitidos.
    allow_headers=["*"],  # Permitir todos los encabezados; puedes especificar los encabezados permitidos.
)

app.include_router(auth_router,       prefix="/auth")
app.include_router(estados_router)
app.include_router(contactos_router)
app.include_router(logs_router)
app.include_router(kpis_router)

BASE.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        reload=True
    )
