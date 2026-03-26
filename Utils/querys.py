from Utils.tools import Tools, CustomException
from Utils.file_handler import FileHandler
from sqlalchemy import text, func, case, extract, and_, or_, Date, cast
from datetime import datetime, date
import json
import traceback
import os
from pathlib import Path
import pytz
from Models.IntranetCarteraUsuariosModel import IntranetCarteraUsuariosModel

import hashlib

class Querys:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.query_params = dict()
        self.colombia_tz = pytz.timezone('America/Bogota')

    def get_usuario_por_email(self, email: str):
        
        """Retorna el usuario activo que coincida con el email, o None."""
        try:
            query = self.db.query(IntranetCarteraUsuariosModel).filter(
                IntranetCarteraUsuariosModel.email  == email,
                IntranetCarteraUsuariosModel.estado == 1
            ).first()
            
            return query
        except Exception as e:
            traceback.print_exc()
            print(f"Error al obtener usuario por email: {e}")
            raise CustomException(f"{e}")
        finally:
            self.db.close()

    # ── Estados / Cartera ────────────────────────────────────────────────────

    def listar_cartera(self, fecha_desde: str, fecha_hasta: str, nit: str = None):
        """Consulta cartera de documentos tipo FC en el rango de fechas dado."""
        try:
            query = text("""
                SELECT
                    d.tipo,
                    d.numero,
                    TRY_CONVERT(date, d.fecha)       AS fecha,
                    TRY_CONVERT(date, d.vencimiento) AS vencimiento,
                    (d.valor_total - d.valor_aplicado) AS saldo,
                    t.nombres AS cliente,
                    CAST(t.nit_real AS NVARCHAR(50)) AS nit
                FROM dbo.documentos AS d
                INNER JOIN dbo.terceros AS t ON d.nit = t.nit
                WHERE
                    TRY_CONVERT(date, d.fecha) IS NOT NULL
                    AND TRY_CONVERT(date, d.fecha) BETWEEN :fecha_desde AND :fecha_hasta
                    AND d.tipo = 'FC'
                    AND (d.valor_total - d.valor_aplicado) <> 0
                    AND (:nit IS NULL OR CAST(t.nit_real AS NVARCHAR(50)) = :nit)
                ORDER BY
                    CAST(t.nit_real AS NVARCHAR(50)) ASC,
                    t.nombres ASC,
                    TRY_CONVERT(date, d.vencimiento) ASC
            """)
            return self.db.execute(query, {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "nit": nit,
            }).fetchall()
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando cartera: {e}")

    def obtener_whatsapp(self, nit: str):
        """Busca el número WhatsApp de un NIT en CRM_contactos."""
        try:
            query = text("""
                SELECT TOP 1
                    c.tel_celular
                FROM dbo.CRM_contactos AS c
                WHERE
                    CAST(c.nit AS NVARCHAR(50)) = :nit
                    AND c.nombre IS NOT NULL
                    AND LTRIM(RTRIM(c.nombre)) LIKE '%Whatsapp%'
                    AND c.tel_celular IS NOT NULL
                    AND LTRIM(RTRIM(c.tel_celular)) <> ''
                ORDER BY c.contacto ASC
            """)
            row = self.db.execute(query, {"nit": str(nit)}).fetchone()
            if not row:
                return None
            numero = str(row.tel_celular).strip()
            for ch in [" ", "-", "+", "(", ")", "."]:
                numero = numero.replace(ch, "")
            if not numero:
                return None
            return numero if numero.startswith("57") else f"57{numero}"
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error obteniendo WhatsApp: {e}")

    def insertar_log(self, nit: str, cliente: str, whatsapp: str, estado_envio: str,
                     mensaje_api: str = "", id_mensaje_whatsapp: str = None,
                     nombre_archivo_pdf: str = None, ruta_pdf: str = None,
                     fecha_corte=None, cantidad_facturas: int = None,
                     valor_total: float = None, nombre_contacto_whatsapp: str = None,
                     fecha_desde=None, fecha_hasta=None):
        """Inserta un registro en la tabla de log de envíos."""
        try:
            self.db.execute(text("""
                INSERT INTO dbo.envios_whatsapp_log (
                    nit, cliente, whatsapp, nombre_contacto_whatsapp,
                    fecha_corte, fecha_desde, fecha_hasta,
                    cantidad_facturas, valor_total,
                    ruta_pdf, nombre_archivo_pdf,
                    estado_envio, mensaje_api, id_mensaje_whatsapp, usuario_envio
                ) VALUES (
                    :nit, :cliente, :whatsapp, :nombre_contacto_whatsapp,
                    :fecha_corte, :fecha_desde, :fecha_hasta,
                    :cantidad_facturas, :valor_total,
                    :ruta_pdf, :nombre_archivo_pdf,
                    :estado_envio, :mensaje_api, :id_mensaje_whatsapp, :usuario_envio
                )
            """), {
                "nit":                      nit,
                "cliente":                  cliente,
                "whatsapp":                 whatsapp,
                "nombre_contacto_whatsapp": nombre_contacto_whatsapp,
                "fecha_corte":              fecha_corte or None,
                "fecha_desde":              fecha_desde or None,
                "fecha_hasta":              fecha_hasta or None,
                "cantidad_facturas":        cantidad_facturas,
                "valor_total":              valor_total,
                "ruta_pdf":                 ruta_pdf,
                "nombre_archivo_pdf":       nombre_archivo_pdf,
                "estado_envio":             estado_envio,
                "mensaje_api":              mensaje_api or None,
                "id_mensaje_whatsapp":      id_mensaje_whatsapp,
                "usuario_envio":            "sistema",
            })
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error insertando log: {e}")

    def tiene_promesa_pago_reciente(self, nit: str) -> bool:
        """Devuelve True si el cliente tiene promesa de pago en los últimos 7 días."""
        try:
            row = self.db.execute(text("""
                IF OBJECT_ID('dbo.gestiones_cartera') IS NULL
                    SELECT TOP 0 1 AS existe
                ELSE
                    SELECT TOP 1 1 AS existe
                    FROM dbo.gestiones_cartera
                    WHERE nit = :nit
                      AND clasificacion_ia = 'promesa_pago'
                      AND created_at >= DATEADD(day, -7, GETDATE())
                    ORDER BY id DESC
            """), {"nit": nit}).fetchone()
            return row is not None
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error verificando promesa de pago: {e}")

    def get_kpis(self):
        """Retorna totales de envíos, enviados y fallidos."""
        try:
            row = self.db.execute(text("""
                SELECT
                    COUNT(*) AS total_envios,
                    SUM(CASE WHEN estado_envio = 'Enviado' THEN 1 ELSE 0 END) AS enviados,
                    SUM(CASE WHEN estado_envio = 'Fallido' THEN 1 ELSE 0 END) AS fallidos
                FROM dbo.envios_whatsapp_log
            """)).fetchone()
            return row
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error calculando KPIs: {e}")

    # ── Gestiones ────────────────────────────────────────────────────────────
    def insertar_gestion(self, nit: str, cliente: str, resultado: str, facturas: str,
                         fecha_compromiso_pago, observacion: str,
                         usuario_gestion: str, clasificacion_ia: str):
        """Inserta una gestión de cartera."""
        try:
            self.db.execute(text("""
                INSERT INTO dbo.gestiones_cartera
                    (nit, cliente, resultado, fecha_compromiso_pago, observacion,
                     facturas, usuario_gestion, clasificacion_ia)
                VALUES
                    (:nit, :cliente, :resultado, :fecha_compromiso_pago, :observacion,
                     :facturas, :usuario_gestion, :clasificacion_ia)
            """), {
                "nit":                   nit,
                "cliente":               cliente,
                "resultado":             resultado,
                "fecha_compromiso_pago": fecha_compromiso_pago or None,
                "observacion":           observacion or None,
                "facturas":              facturas or None,
                "usuario_gestion":       usuario_gestion or "sistema",
                "clasificacion_ia":      clasificacion_ia or None,
            })
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error insertando gestión: {e}")

    def existe_gestion_hoy(self, nit: str, resultado: str) -> bool:
        """Retorna True si ya existe una gestión con ese nit+resultado registrada hoy."""
        try:
            row = self.db.execute(text("""
                IF OBJECT_ID('dbo.gestiones_cartera') IS NULL
                    SELECT 0 AS existe
                ELSE
                    SELECT TOP 1 1 AS existe
                    FROM dbo.gestiones_cartera
                    WHERE nit = :nit
                      AND resultado = :resultado
                      AND CONVERT(DATE, created_at) = CONVERT(DATE, GETDATE())
            """), {"nit": nit, "resultado": resultado}).fetchone()
            return row is not None and int(row.existe or 0) == 1
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error verificando gestión duplicada: {e}")

    def get_gestion_hoy(self, nit: str):
        """Retorna la gestión más reciente registrada hoy para el NIT, o None."""
        try:
            row = self.db.execute(text("""
                IF OBJECT_ID('dbo.gestiones_cartera') IS NULL
                    SELECT TOP 0
                        CAST(NULL AS NVARCHAR(100)) AS resultado,
                        CAST(NULL AS NVARCHAR(MAX)) AS observacion,
                        CAST(NULL AS NVARCHAR(10))  AS fecha_compromiso_pago,
                        CAST(NULL AS NVARCHAR(100)) AS clasificacion_ia,
                        CAST(NULL AS NVARCHAR(100)) AS usuario_gestion
                ELSE
                    SELECT TOP 1
                        resultado,
                        observacion,
                        CONVERT(NVARCHAR(10), fecha_compromiso_pago, 23) AS fecha_compromiso_pago,
                        clasificacion_ia,
                        usuario_gestion
                    FROM dbo.gestiones_cartera
                    WHERE nit = :nit
                      AND CONVERT(DATE, created_at) = CONVERT(DATE, GETDATE())
                    ORDER BY id DESC
            """), {"nit": nit}).fetchone()
            if not row or not row.resultado:
                return None
            return {
                "resultado":             row.resultado,
                "observacion":           row.observacion,
                "fecha_compromiso_pago": row.fecha_compromiso_pago,
                "clasificacion_ia":      row.clasificacion_ia,
                "usuario_gestion":       row.usuario_gestion,
            }
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error obteniendo gestión del día: {e}")
    def listar_gestiones_nit(self, nit: str):
        """Retorna todas las gestiones registradas para un NIT, ordenadas de más recientes a más antiguas."""
        try:
            rows = self.db.execute(text("""
                IF OBJECT_ID('dbo.gestiones_cartera') IS NULL
                    SELECT TOP 0
                        CAST(NULL AS INT)           AS id,
                        CAST(NULL AS NVARCHAR(100)) AS resultado,
                        CAST(NULL AS NVARCHAR(MAX)) AS observacion,
                        CAST(NULL AS NVARCHAR(10))  AS fecha_compromiso_pago,
                        CAST(NULL AS NVARCHAR(100)) AS clasificacion_ia,
                        CAST(NULL AS NVARCHAR(100)) AS usuario_gestion,
                        CAST(NULL AS NVARCHAR(23))  AS created_at
                ELSE
                    SELECT
                        id,
                        resultado,
                        observacion,
                        CONVERT(NVARCHAR(10), fecha_compromiso_pago, 23) AS fecha_compromiso_pago,
                        clasificacion_ia,
                        usuario_gestion,
                        CONVERT(NVARCHAR(23), created_at, 126) AS created_at
                    FROM dbo.gestiones_cartera
                    WHERE nit = :nit
                    ORDER BY id DESC
            """), {"nit": nit}).fetchall()
            return [
                {
                    "id":                    r.id,
                    "resultado":             r.resultado,
                    "observacion":           r.observacion,
                    "fecha_compromiso_pago": r.fecha_compromiso_pago,
                    "clasificacion_ia":      r.clasificacion_ia,
                    "usuario_gestion":       r.usuario_gestion,
                    "created_at":            r.created_at,
                }
                for r in rows
            ]
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando historial de gestiones: {e}")
    # ── Logs ───────────────────────────────────────────────────────────────

    def listar_logs(self, limite: int = 200, nit: str = None, estado: str = None):
        """Retorna el historial de envíos WhatsApp con filtros opcionales."""
        try:
            rows = self.db.execute(text("""
                SELECT TOP (:limite)
                    id,
                    nit,
                    cliente,
                    whatsapp,
                    nombre_contacto_whatsapp,
                    CONVERT(NVARCHAR(10), fecha_corte, 23)  AS fecha_corte,
                    cantidad_facturas,
                    valor_total,
                    nombre_archivo_pdf,
                    ruta_pdf,
                    estado_envio,
                    mensaje_api,
                    id_mensaje_whatsapp,
                    usuario_envio,
                    CONVERT(NVARCHAR(23), fecha_envio, 126) AS fecha_envio
                FROM dbo.envios_whatsapp_log
                WHERE
                    (:nit    IS NULL OR nit          = :nit)
                    AND (:estado IS NULL OR estado_envio = :estado)
                ORDER BY fecha_envio DESC
            """), {
                "limite": limite,
                "nit":    nit or None,
                "estado": estado or None,
            }).fetchall()
            return [
                {
                    "id":                      r.id,
                    "nit":                     r.nit,
                    "cliente":                 r.cliente,
                    "whatsapp":                r.whatsapp,
                    "nombre_contacto_whatsapp": r.nombre_contacto_whatsapp,
                    "fecha_corte":             r.fecha_corte,
                    "cantidad_facturas":        r.cantidad_facturas,
                    "valor_total":             float(r.valor_total) if r.valor_total is not None else None,
                    "nombre_archivo_pdf":       r.nombre_archivo_pdf,
                    "ruta_pdf":                r.ruta_pdf,
                    "estado_envio":            r.estado_envio,
                    "mensaje_api":             r.mensaje_api,
                    "id_mensaje_whatsapp":     r.id_mensaje_whatsapp,
                    "usuario_envio":           r.usuario_envio,
                    "fecha_envio":             r.fecha_envio,
                }
                for r in rows
            ]
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando logs: {e}")

    # ── Contactos ──────────────────────────────────────────────────────────

    def buscar_contactos(self, nit: str = None):
        """Busca contactos en CRM_contactos. Si nit es None retorna los últimos 100."""
        try:
            if nit:
                query = text("""
                    SELECT
                        CAST(c.nit AS NVARCHAR(50)) AS nit,
                        c.nombre,
                        c.tel_celular
                    FROM dbo.CRM_contactos AS c
                    WHERE CAST(c.nit AS NVARCHAR(50)) = :nit
                    ORDER BY c.contacto ASC
                """)
                rows = self.db.execute(query, {"nit": str(nit)}).fetchall()
            else:
                query = text("""
                    SELECT TOP 100
                        CAST(c.nit AS NVARCHAR(50)) AS nit,
                        c.nombre,
                        c.tel_celular
                    FROM dbo.CRM_contactos AS c
                    ORDER BY c.contacto DESC
                """)
                rows = self.db.execute(query).fetchall()
            return [
                {"nit": r.nit, "nombre": r.nombre, "tel_celular": r.tel_celular}
                for r in rows
            ]
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando CRM_contactos: {e}")

    def actualizar_contacto_whatsapp(self, nit: str, tel_celular: str) -> bool:
        """Actualiza tel_celular en el registro WhatsApp existente. Retorna True si hubo filas afectadas."""
        try:
            result = self.db.execute(text("""
                UPDATE dbo.CRM_contactos
                SET tel_celular = :tel_celular
                WHERE CAST(nit AS NVARCHAR(50)) = :nit
                  AND LTRIM(RTRIM(nombre)) LIKE '%Whatsapp%'
            """), {"nit": str(nit), "tel_celular": str(tel_celular)})
            self.db.commit()
            return (result.rowcount or 0) > 0
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error actualizando contacto: {e}")

    def insertar_contacto_whatsapp(self, nit: str, nombre: str, tel_celular: str):
        """Inserta un nuevo contacto WhatsApp en CRM_contactos usando metadatos dinámicos."""
        try:
            # Leer columnas de la tabla para hacer un INSERT segúro
            meta = self.db.execute(text("""
                SELECT
                    c.name AS column_name,
                    t.name AS type_name,
                    COLUMNPROPERTY(c.object_id, c.name, 'IsIdentity') AS is_identity,
                    c.is_nullable
                FROM sys.columns c
                INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
                WHERE c.object_id = OBJECT_ID('dbo.CRM_contactos')
                ORDER BY c.column_id
            """)).fetchall()

            # Calcular siguiente consecutivo de contacto para este NIT
            row_max = self.db.execute(text("""
                SELECT ISNULL(MAX(contacto), 0) AS max_contacto
                FROM dbo.CRM_contactos
                WHERE CAST(nit AS NVARCHAR(50)) = :nit
            """), {"nit": str(nit)}).fetchone()
            siguiente_contacto = int(row_max.max_contacto or 0) + 1

            provided = {
                "nit":         str(nit),
                "nombre":      str(nombre or "Whatsapp"),
                "tel_celular": str(tel_celular),
                "contacto":    siguiente_contacto,
            }

            insert_cols, values_sql, params = [], [], {}
            for col in meta:
                if col.is_identity == 1:
                    continue
                col_name = col.column_name
                if col_name in provided:
                    insert_cols.append(col_name)
                    values_sql.append(f":{col_name}")
                    params[col_name] = provided[col_name]
                    continue
                if col.is_nullable:
                    continue
                # columna NOT NULL sin valor provisto: usar default según tipo
                t = col.type_name.lower()
                if t in {"date", "datetime", "datetime2", "smalldatetime"}:
                    insert_cols.append(col_name)
                    values_sql.append("GETDATE()")
                else:
                    insert_cols.append(col_name)
                    values_sql.append(f":{col_name}")
                    params[col_name] = 0 if t in {"int", "bigint", "smallint", "bit", "decimal", "numeric", "float"} else ""

            sql = f"INSERT INTO dbo.CRM_contactos ({', '.join(insert_cols)}) VALUES ({', '.join(values_sql)})"
            self.db.execute(text(sql), params)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error insertando contacto: {e}")
