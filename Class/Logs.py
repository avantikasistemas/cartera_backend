from Utils.tools import Tools
from Utils.querys import Querys
from Utils.tools import CustomException


class Logs:
    def __init__(self, db):
        self.tools  = Tools()
        self.querys = Querys(db)

    # ── Listar historial ──────────────────────────────────────────────────

    def listar(self, data: dict):
        limite = int(data.get("limite") or 200)
        nit    = (data.get("nit") or "").strip() or None
        estado = (data.get("estado") or "").strip() or None

        logs = self.querys.listar_logs(limite=limite, nit=nit, estado=estado)
        return self.tools.output(200, "Logs obtenidos", logs)
