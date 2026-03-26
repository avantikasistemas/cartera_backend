from Config.db import BASE
from sqlalchemy import Column, String, Integer, Date, DateTime, Text
from datetime import datetime


class IntranetCarteraGestionesModel(BASE):

    __tablename__ = "gestiones_cartera"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    nit                   = Column(String(50),  nullable=False)
    cliente               = Column(String(255), nullable=False)
    resultado             = Column(String(100), nullable=False)
    fecha_compromiso_pago = Column(Date,        nullable=True)
    observacion           = Column(Text,        nullable=True)
    facturas              = Column(String(500), nullable=True)   # números separados por coma
    usuario_gestion       = Column(String(100), nullable=True)
    clasificacion_ia      = Column(String(100), nullable=True)
    created_at            = Column(DateTime, default=datetime.now)

    def __init__(self, data: dict):
        self.nit                   = data['nit']
        self.cliente               = data['cliente']
        self.resultado             = data['resultado']
        self.fecha_compromiso_pago = data.get('fecha_compromiso_pago')
        self.observacion           = data.get('observacion')
        self.facturas              = data.get('facturas')
        self.usuario_gestion       = data.get('usuario_gestion')
        self.clasificacion_ia      = data.get('clasificacion_ia')

    def to_dict(self):
        return {
            'id':                    self.id,
            'nit':                   self.nit,
            'cliente':               self.cliente,
            'resultado':             self.resultado,
            'fecha_compromiso_pago': self.fecha_compromiso_pago.isoformat() if self.fecha_compromiso_pago else None,
            'observacion':           self.observacion,
            'facturas':              self.facturas,
            'usuario_gestion':       self.usuario_gestion,
            'clasificacion_ia':      self.clasificacion_ia,
            'created_at':            self.created_at.isoformat() if self.created_at else None,
        }
