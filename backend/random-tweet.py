import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "secret123")  # 🔑 Token definido en tu .env

# Headers con autorización
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

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

# Request GET con autorización por header
response = requests.get(endpoint, headers=headers)

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

# Publicar el tweet con el mismo header de autorización
post_url = API_BASE + "/tweets/post"
res = requests.post(post_url, headers=headers, json={"text": texto})
if res.status_code != 200:
    raise Exception(f"❌ Error al postear: {res.status_code} - {res.text}")

print("✅ Tweet publicado con éxito")
