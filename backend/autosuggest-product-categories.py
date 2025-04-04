import os
import httpx
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, Category
from dotenv import load_dotenv

load_dotenv()
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

BATCH_SIZE = 20

def get_uncategorized_products(session: Session):
    return (
        session.query(Product)
        .filter(Product.category_id == None)
        .order_by(Product.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )

def get_categories(session: Session):
    return session.query(Category).all()

def ask_deepseek(titles, category_names):
    system = "Sos un clasificador. Te paso una lista de títulos de productos y las categorías disponibles. Indicá a cuál categoría pertenece cada producto. Respondé una lista en formato JSON."
    user = {
        "productos": titles,
        "categorias": category_names
    }
    prompt = f"""Productos: {titles}
Categorías disponibles: {', '.join(category_names)}
Devolvé un JSON con: [{{"title": "...", "categoria": "..."}}]"""

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
        timeout=60
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

def main():
    session = SessionLocal()
    try:
        products = get_uncategorized_products(session)
        categories = get_categories(session)
        category_map = {c.name.lower(): c.id for c in categories}

        titles = [p.title for p in products]
        suggestions_raw = ask_deepseek(titles, list(category_map.keys()))

        import json
        import re

        # 1. Log raw content (opcional pero recomendable)
        print("🔍 Respuesta raw de DeepSeek:")
        print(suggestions_raw)

        # 2. Intentar extraer JSON entre corchetes
        json_match = re.search(r"\[\s*{.*}\s*]", suggestions_raw, re.DOTALL)

        if not json_match:
            raise Exception("❌ No se encontró una estructura JSON válida en la respuesta de DeepSeek")

        try:
            suggestions = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print("❗ Error al parsear JSON extraído:")
            print(json_match.group(0))
            raise e


        applied = []
        for suggestion in suggestions:
            title = suggestion["title"]
            cat_name = suggestion["categoria"].lower()
            product = next((p for p in products if p.title == title), None)
            if product and cat_name in category_map:
                product.category_id = category_map[cat_name]
                print(f"Aplicando sugerencia: {title} → {cat_name}")
                applied.append((product.title, cat_name))
        session.commit()

        with open("deepseek_suggestions_report.md", "w") as f:
            f.write("# Sugerencias aplicadas por DeepSeek\n\n")
            for title, cat in applied:
                f.write(f"- `{title}` → **{cat}**\n")

        print(f"{len(applied)} sugerencias aplicadas.")
    finally:
        session.close()

if __name__ == "__main__":
    main()
