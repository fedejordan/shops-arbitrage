import os
from dotenv import load_dotenv

load_dotenv()

from requests_oauthlib import OAuth1Session

# Tus claves (las podés guardar en variables de entorno si querés)
consumer_key = os.getenv("X_API_KEY")
consumer_secret = os.getenv("X_API_KEY_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

# Crear sesión autenticada
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

# Payload con el tweet
payload = {"text": "¡TuPrecioIdeal ahora también twittea solo 🚀🧠!"}

# Hacer el posteo
response = oauth.post(
    "https://api.twitter.com/2/tweets",
    json=payload,
)

if response.status_code != 201:
    raise Exception(f"Error {response.status_code}: {response.text}")

print("Tweet publicado con éxito ✅")
