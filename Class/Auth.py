import jwt
import os
from datetime import datetime, timedelta, timezone
from Utils.tools import Tools
from Utils.querys import Querys

JWT_SECRET    = os.getenv("JWT_SECRET", "cambia-este-secreto")
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = 8


class Auth:

    def __init__(self, db):
        self.db    = db
        self.tools = Tools()
        self.querys = Querys(db)

    def login(self, data: dict):

        email    = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return self.tools.output(400, "Email y contraseña son requeridos")

        user = self.querys.get_usuario_por_email(email)

        # Respuesta genérica para no revelar cuál campo falló
        if not user:
            return self.tools.output(401, "Credenciales incorrectas")

        if user.password != password:
            return self.tools.output(401, "Credenciales incorrectas")

        token = jwt.encode(
            {
                "user_id": user.id,
                "email":   user.email,
                "nombre":  user.nombre,
                "exp":     datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        return self.tools.output(200, "Login exitoso", {
            "token":  token,
            "nombre": user.nombre,
            "email":  user.email,
        })
