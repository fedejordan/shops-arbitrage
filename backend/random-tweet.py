import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

# Crear una sesión para mantener la cookie
session = requests.Session()

# Login para obtener la cookie admin_token
login_response = session.post(
    API_BASE + "/admin/login-check",
    json={"username": ADMIN_USER, "password": ADMIN_PASSWORD}
)

if login_response.status_code != 200:
    raise Exception(f"❌ Error de login: {login_response.status_code} - {login_response.text}")

print("🔐 Login exitoso. Cookie guardada.")

# Endpoints disponibles para obtener sugerencias de tweets
sources = [
    "/tweets/suggestions",
    "/tweets/discounts",
    "/tweets/top-discounts",
    "/tweets/historical-difference",
    "/tweets/educational"
]

# Selecciona aleatoriamente uno
endpoint = API_BASE + random.choice(sources)
print(f"🔍 Fetching from: {endpoint}")

# Usamos la misma sesión para mantener cookies
response = session.get(endpoint)

if response.status_code != 200:
    raise Exception(f"❌ Error al obtener sugerencias: {response.status_code} - {response.text}")

data = response.json()

# Según la estructura del endpoint, extraemos los textos
candidatos = []
if isinstance(data, list):
    for entry in data:
        if isinstance(entry, dict) and "tweets" in entry:
            candidatos.extend(entry["tweets"])
        elif isinstance(entry, str):
            candidatos.append(entry)
elif isinstance(data, dict) and "tweets" in data:
    candidatos.extend(data["tweets"])

if not candidatos:
    raise Exception("❌ No se encontraron tweets sugeridos.")

texto = random.choice(candidatos)
print(f"📢 Tweet seleccionado: {texto}")

# Publicar el tweet usando la misma sesión
post_url = API_BASE + "/tweets/post"
res = session.post(post_url, json={"text": texto})
if res.status_code != 200:
    raise Exception(f"❌ Error al postear: {res.status_code} - {res.text}")

print("✅ Tweet publicado con éxito")
