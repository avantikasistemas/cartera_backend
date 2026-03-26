from Utils.tools import Tools
from Utils.querys import Querys


class Kpis:
    def __init__(self, db):
        self.tools  = Tools()
        self.querys = Querys(db)

    # ── KPIs generales ────────────────────────────────────────────────────

    def listar(self, data: dict):
        row = self.querys.get_kpis()

        total    = int(row.total_envios or 0)
        enviados = int(row.enviados     or 0)
        fallidos = int(row.fallidos     or 0)
        efectividad = round((enviados / total) * 100, 2) if total > 0 else 0

        return self.tools.output(200, "KPIs obtenidos", {
            "total_envios": total,
            "enviados":     enviados,
            "fallidos":     fallidos,
            "efectividad":  efectividad,
        })
