import jwt
import datetime

# Credenciales del usuario administrador de Odoo
email = "yo@mail.com"
password = "admin"

# Generar token JWT válido por 1 día
payload = {
    "sub": email,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
}

# Clave secreta (normalmente estaría en una variable de entorno)
# Usamos una clave simple para pruebas
secret_key = "your-secret-key"

# Generar token
token = jwt.encode(payload, secret_key, algorithm="HS256")

print(f"Token JWT generado: {token}")