from collections import defaultdict
from datetime import datetime
from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from Utils.pdf_service import generar_pdf
from Utils.whatsapp_service import enviar_documento
from Utils.ia_service import clasificar_respuesta


class Estados:

    def __init__(self, db):
        self.db     = db
        self.tools  = Tools()
        self.querys = Querys(db)

    # ── Cartera ──────────────────────────────────────────────────────────────

    def listar(self, data: dict):
        fecha_desde = data.get("fecha_desde", "").strip()
        fecha_hasta = data.get("fecha_hasta", "").strip()
        nit         = data.get("nit", "").strip() or None

        if not fecha_desde or not fecha_hasta:
            return self.tools.output(400, "fecha_desde y fecha_hasta son requeridos")

        try:
            datetime.strptime(fecha_desde, "%Y-%m-%d")
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
        except ValueError:
            return self.tools.output(400, "Las fechas deben estar en formato YYYY-MM-DD")

        rows = self.querys.listar_cartera(fecha_desde, fecha_hasta, nit)

        clientes = defaultdict(list)
        for row in rows:
            clientes[(row.nit, row.cliente)].append({
                "tipo":       row.tipo,
                "numero":     str(row.numero),
                "fecha":      row.fecha.isoformat() if row.fecha else None,
                "vencimiento": row.vencimiento.isoformat() if row.vencimiento else None,
                "saldo":      float(row.saldo or 0),
            })

        resultado = []
        for (nit_cli, nombre_cli), facturas in clientes.items():
            whatsapp     = self.querys.obtener_whatsapp(nit_cli)
            gestion_hoy  = self.querys.get_gestion_hoy(nit_cli)
            resultado.append({
                "nit":         nit_cli,
                "cliente":     nombre_cli,
                "whatsapp":    whatsapp,
                "facturas":    facturas,
                "gestion_hoy": gestion_hoy,
                "historial":   None,
            })

        return self.tools.output(200, "Cartera obtenida", resultado)

    # ── PDF ──────────────────────────────────────────────────────────────────

    def generar_pdf(self, data: dict):
        cliente    = data.get("cliente")
        nit        = data.get("nit")
        facturas   = data.get("facturas", [])
        fecha_corte = data.get("fecha_corte")

        if not cliente or not nit:
            return self.tools.output(400, "cliente y nit son requeridos")

        result = generar_pdf(cliente, nit, facturas, fecha_corte)
        return self.tools.output(200, "PDF generado", {
            "filename": result["filename"],
            "url": f"/Uploads/{result['filename']}",
        })

    # ── Envío individual ─────────────────────────────────────────────────────

    def enviar(self, data: dict):
        cliente    = data.get("cliente")
        nit        = data.get("nit")
        whatsapp   = data.get("whatsapp")
        facturas   = data.get("facturas", [])
        fecha_corte = data.get("fecha_corte")

        if not cliente or not nit or not whatsapp:
            return self.tools.output(400, "cliente, nit y whatsapp son requeridos")

        pdf   = generar_pdf(cliente, nit, facturas, fecha_corte)
        envio = enviar_documento(whatsapp, pdf["filename"])

        estado_envio = "Enviado" if envio.get("ok") else "Fallido"
        _msgs = (envio.get("data") or {}).get("messages") or []
        self.querys.insertar_log(
            nit=nit,
            cliente=cliente,
            whatsapp=whatsapp,
            estado_envio=estado_envio,
            mensaje_api=str(envio.get("data") or envio.get("message", "")),
            id_mensaje_whatsapp=_msgs[0].get("id") if _msgs else None,
            nombre_archivo_pdf=pdf["filename"],
            ruta_pdf=f"/Uploads/{pdf['filename']}",
            fecha_corte=fecha_corte,
            cantidad_facturas=len(facturas),
            valor_total=sum(float(f.get("saldo", 0)) for f in facturas),
        )

        return self.tools.output(200, "Envío procesado", {
            "ok":      envio.get("ok"),
            "envio":   envio,
            "pdf_url": f"/Uploads/{pdf['filename']}",
        })

    # ── Envío masivo ─────────────────────────────────────────────────────────

    def enviar_masivo(self, data: dict):
        clientes    = data.get("clientes", [])
        fecha_corte = data.get("fecha_corte")
        enviados    = 0
        omitidos    = 0
        errores     = 0
        detalle     = []

        for item in clientes:
            nit      = item.get("nit")
            cliente  = item.get("cliente")
            whatsapp = item.get("whatsapp")
            facturas = item.get("facturas", [])

            # Omitir si tiene promesa de pago reciente (automatización inteligente)
            if self.querys.tiene_promesa_pago_reciente(nit):
                omitidos += 1
                detalle.append({"nit": nit, "cliente": cliente, "estado": "omitido_promesa_pago"})
                continue

            if not whatsapp:
                errores += 1
                detalle.append({"nit": nit, "cliente": cliente, "estado": "sin_whatsapp"})
                continue

            pdf   = generar_pdf(cliente, nit, facturas, fecha_corte)
            envio = enviar_documento(whatsapp, pdf["filename"])
            estado_envio = "Enviado" if envio.get("ok") else "Fallido"

            if envio.get("ok"):
                enviados += 1
            else:
                errores += 1

            _msgs = (envio.get("data") or {}).get("messages") or []
            self.querys.insertar_log(
                nit=nit,
                cliente=cliente,
                whatsapp=whatsapp,
                estado_envio=estado_envio,
                mensaje_api=str(envio.get("data") or envio.get("message", "")),
                id_mensaje_whatsapp=_msgs[0].get("id") if _msgs else None,
                nombre_archivo_pdf=pdf["filename"],
                ruta_pdf=f"/Uploads/{pdf['filename']}",
                fecha_corte=fecha_corte,
                cantidad_facturas=len(facturas),
                valor_total=sum(float(f.get("saldo", 0)) for f in facturas),
            )
            detalle.append({"nit": nit, "cliente": cliente, "estado": estado_envio.lower()})

        return self.tools.output(200, "Envío masivo procesado", {
            "enviados": enviados,
            "omitidos": omitidos,
            "errores":  errores,
            "detalle":  detalle,
        })

    # ── Gestiones ─────────────────────────────────────────────────────────────

    def crear_gestion(self, data: dict):
        nit                   = data.get("nit", "").strip()
        cliente               = data.get("cliente", "").strip()
        resultado             = data.get("resultado", "").strip()
        fecha_compromiso_pago = data.get("fecha_compromiso_pago") or None
        observacion           = data.get("observacion") or None
        usuario_gestion       = data.get("usuario_gestion", "sistema")
        facturas_lista        = data.get("facturas", [])  # lista de dicts o strings

        if not nit or not cliente or not resultado:
            return self.tools.output(400, "nit, cliente y resultado son requeridos")

        # Convertir lista de facturas → números separados por coma
        if isinstance(facturas_lista, list):
            numeros = [str(f.get("numero", f) if isinstance(f, dict) else f) for f in facturas_lista]
            facturas_str = ",".join(filter(None, numeros))
        else:
            facturas_str = str(facturas_lista) if facturas_lista else None

        # Clasificación IA basada en resultado + observación
        texto_ia = f"{resultado}. {observacion or ''}"
        clasificacion = clasificar_respuesta(texto_ia)

        self.querys.insertar_gestion(
            nit=nit,
            cliente=cliente,
            resultado=resultado,
            facturas=facturas_str,
            fecha_compromiso_pago=fecha_compromiso_pago,
            observacion=observacion,
            usuario_gestion=usuario_gestion,
            clasificacion_ia=clasificacion.get("tipo"),
        )

        return self.tools.output(200, "Gestión guardada correctamente", {
            "clasificacion_ia": clasificacion,
        })
    # ── Historial de gestiones ──────────────────────────────────────────────

    def listar_historial_gestiones(self, data: dict):
        nit = (data.get("nit") or "").strip()
        if not nit:
            return self.tools.output(400, "nit es requerido")
        gestiones = self.querys.listar_gestiones_nit(nit)
        return self.tools.output(200, "Historial de gestiones obtenido", gestiones)
    # ── KPIs ─────────────────────────────────────────────────────────────────

    def kpis(self):
        row = self.querys.get_kpis()
        total    = int(row.total_envios or 0)
        enviados = int(row.enviados or 0)
        fallidos = int(row.fallidos or 0)
        efectividad = round((enviados / total) * 100, 2) if total > 0 else 0

        return self.tools.output(200, "KPIs obtenidos", {
            "total_envios": total,
            "enviados":     enviados,
            "fallidos":     fallidos,
            "efectividad":  efectividad,
        })
