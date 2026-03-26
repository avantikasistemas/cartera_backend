from Utils.tools import Tools
from Utils.querys import Querys
from Utils.tools import CustomException


class Contactos:
    def __init__(self, db):
        self.db     = db
        self.tools  = Tools()
        self.querys = Querys(db)


    # ── Listar / buscar ───────────────────────────────────────────────────

    def listar(self, data: dict):
        nit = (data.get("nit") or "").strip()
        if not nit:
            raise CustomException("El campo nit es obligatorio")
        contactos = self.querys.buscar_contactos(nit=nit)
        if not contactos:
            raise CustomException("No se encontraron contactos para el NIT indicado", code=404)
        return self.tools.output(200, "Contactos obtenidos", contactos)

    # ── Crear / actualizar (upsert) ───────────────────────────────────────

    def crear(self, data: dict):
        nit       = str(data.get("nit", "")).strip()
        tel       = str(data.get("tel_celular", "")).strip()
        nombre    = str(data.get("nombre", "Whatsapp")).strip() or "Whatsapp"

        if not nit:
            raise CustomException("El campo nit es obligatorio")
        if not tel:
            raise CustomException("El campo tel_celular es obligatorio")

        actualizado = self.querys.actualizar_contacto_whatsapp(nit=nit, tel_celular=tel)
        if actualizado:
            return self.tools.output(200, "Contacto actualizado", {"mode": "updated", "nit": nit})

        self.querys.insertar_contacto_whatsapp(nit=nit, nombre=nombre, tel_celular=tel)
        return self.tools.output(201, "Contacto creado", {"mode": "created", "nit": nit})
