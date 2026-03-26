from Config.db import BASE
from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, Index
from datetime import datetime

class IntranetCarteraUsuariosModel(BASE):

    __tablename__= "intranet_cartera_usuarios"
    
    id          = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(200))
    email       = Column(String(200))
    password    = Column(String(255))
    estado      = Column(Integer, default=1)  # 1 = activo
    created_at  = Column(DateTime, default=datetime.now)
    updated_at  = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, data: dict):
        self.nombre = data['nombre']
        self.email = data['email']
        self.password = data['password']

    def to_dict(self):
        """Convierte el modelo a diccionario para serialización JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'estado': self.estado
        }
