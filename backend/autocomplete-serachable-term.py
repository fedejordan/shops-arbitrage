import os
import httpx
import re
import time
import json
import unicodedata
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product
from dotenv import load_dotenv

load_dotenv()
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

BATCH_SIZE = 20

# Regex para detectar posibles códigos de modelo
MODEL_REGEX = re.compile(r"\b[A-Z]{2,}-?\d+[A-Z0-9\-]*\b")

def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = " ".join(text.split())
    return text

def get_products_missing_searchable_term(session: Session):
    return (
        session.query(Product)
        .filter(Product.searchable_term == None)
        .order_by(Product.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )

def count_products_missing_searchable_term(session: Session):
    return session.query(Product).filter(Product.searchable_term == None).count()

GENERIC_TERMS = {"PS4", "PS5", "XBOX", "TV", "LED", "UHD", "FULLHD", "HD", "4K", "WI-FI"}

def extract_model_with_regex(title: str) -> str | None:
    matches = MODEL_REGEX.findall(title.upper())
    for match in matches:
        if match.upper() not in GENERIC_TERMS:
            return match
    return None

def ask_deepseek_for_searchable_terms(titles: list[str]) -> list[dict[str, str]]:
    system = (
        "Sos un clasificador de productos. Tu tarea es extraer el **modelo específico o identificador único** de cada producto "
        "que permita encontrar el mismo producto en otras tiendas. Evitá términos genéricos como 'PS5', 'TV', 'LED', '4K', etc. "
        "Devolvé sólo el identificador del modelo, no la marca ni la categoría."
    )

    prompt = f"""
    Te paso una lista de títulos de productos. Para cada uno, devolvé el modelo o identificador **específico** (como "G225BT", "SM-A526B", "TN1060"), evitando términos genéricos como:

    - PS4, PS5
    - TV, LED, UHD, 4K, SMART
    - AURICULAR, JOYSTICK
    - BLUETOOTH, WIFI, NEGRO, BLANCO

    Formato de respuesta (JSON):
    [
    {{"title": "Título original", "modelo": "Modelo extraído o vacío si no hay uno válido"}}
    ]

    Ejemplo:
    - Título: "Autostereo Pioneer DMH-G225BT Pantalla Táctil 6,2\" Bluetooth" → modelo: "DMH-G225BT"
    - Título: "Video Juego PS5 Horizon Zero Dawn" → modelo: "Horizon Zero Dawn"
    - Título: "Joystick Sony PS5 DualSense EDGE ZCP1" → modelo: "ZCP1"
    - Título: "Auricular BT XPODS7 negro bluetooth X-View" → modelo: "XPODS7"

    Lista de productos:
    {json.dumps(titles, ensure_ascii=False, indent=2)}
    """


    res = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        },
        timeout=120
    )
    res.raise_for_status()
    return json.loads(re.search(r"\[\s*{.*}\s*]", res.json()["choices"][0]["message"]["content"], re.DOTALL).group(0))

def main():
    session = SessionLocal()
    start_time = time.time()
    try:
        total_missing = count_products_missing_searchable_term(session)
        print(f"🔎 Productos sin 'searchable_term': {total_missing}\n")

        total_applied = 0
        batch_num = 1

        while True:
            print(f"\n🚀 Procesando batch #{batch_num}...")
            products = get_products_missing_searchable_term(session)
            if not products:
                print("✅ No quedan más productos sin searchable_term.")
                break

            to_fill_with_deepseek = []
            deepseek_titles = []

            for product in products:
                model = extract_model_with_regex(product.title)
                if model:
                    if model.upper() in GENERIC_TERMS or len(model) < 3:
                        model = product.title # None  # ignorarlo si es genérico o muy corto
                        print(f"🔧 {product.title} → (full title) → {model}")
                    else:
                        print(f"🔧 {product.title} → (regex) → {model}")
                    product.searchable_term = model
                    
                    total_applied += 1
                else:
                    to_fill_with_deepseek.append(product)
                    deepseek_titles.append(product.title)

            if deepseek_titles:
                print("🧠 Solicitando a DeepSeek para los restantes...")
                try:
                    suggestions = ask_deepseek_for_searchable_terms(deepseek_titles)
                    for suggestion in suggestions:
                        title = suggestion["title"]
                        model = suggestion["modelo"]
                        product = next((p for p in to_fill_with_deepseek if p.title == title), None)
                        if model.upper() in GENERIC_TERMS or len(model) < 3:
                            model = product.title #None  # ignorarlo si es genérico o muy corto
                            print(f"🔧 {product.title} → (full title) → {model}")
                        else:
                            print(f"🔧 {title} → (deepseek) → {model}")
                        if product:
                            product.searchable_term = model
                            
                            total_applied += 1
                except Exception as e:
                    print(f"❌ Error en DeepSeek: {e}")
                    break

            session.commit()
            print(f"✅ Batch #{batch_num} completo. Productos procesados: {len(products)}")
            batch_num += 1
            time.sleep(2)

        elapsed_time = time.time() - start_time
        print(f"\n🎉 Proceso finalizado. Total completados: {total_applied}")
        print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos")

    finally:
        session.close()

if __name__ == "__main__":
    main()
