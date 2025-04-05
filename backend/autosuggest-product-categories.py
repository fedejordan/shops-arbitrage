import os
import httpx
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, Category
from dotenv import load_dotenv
import json
import re
import time

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

    prompt = f"""
A continuación tenés una lista de productos y una lista de categorías disponibles.

Tu tarea es asignar una única categoría a cada producto, eligiendo **solo** de las categorías provistas.

Respondé exclusivamente una lista en formato JSON. Cada elemento debe tener esta estructura:
[
  {{"title": "título del producto", "categoria": "nombre exacto de la categoría"}}
]
Por favor, responde con el title y la categoria exacta que se te proporciona, sin normalizar.
Productos:
{json.dumps(titles, ensure_ascii=False, indent=2)}

Categorías disponibles:
{json.dumps(category_names, ensure_ascii=False, indent=2)}
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
        timeout=120  # mayor timeout por si el prompt crece
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

def main():
    session = SessionLocal()
    start_time = time.time()  # Iniciamos el cronómetro
    try:
        categories = get_categories(session)
        category_map = {c.name.lower(): c.id for c in categories}
        total_applied = 0
        batch_num = 1
        summary_log = []

        while True:
            print(f"\n🚀 Procesando batch #{batch_num}...")
            products = get_uncategorized_products(session)
            if not products:
                print("✅ No quedan más productos sin categorizar.")
                break

            titles = [p.title for p in products]

            try:
                suggestions_raw = ask_deepseek(titles, list(category_map.keys()))
            except Exception as e:
                print(f"❌ Error en batch #{batch_num}: {e}")
                break

            print("🔍 Respuesta raw:")
            print(suggestions_raw)

            json_match = re.search(r"\[\s*{.*}\s*]", suggestions_raw, re.DOTALL)
            if not json_match:
                print("❌ No se encontró JSON válido en la respuesta. Saltando batch.")
                break

            try:
                suggestions = json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                print("❗ Error al parsear JSON:")
                print(json_match.group(0))
                raise e

            applied = []
            for suggestion in suggestions:
                title = suggestion["title"]
                cat_name = suggestion["categoria"].lower()
                product = next((p for p in products if p.title == title), None)
                if product and cat_name in category_map:
                    product.category_id = category_map[cat_name]
                    print(f"✔️ {title} → {cat_name}")
                    applied.append((product.title, cat_name))

            session.commit()
            total_applied += len(applied)

            batch_log = [f"- `{title}` → **{cat}**" for title, cat in applied]
            summary_log.append(f"# Batch #{batch_num}\n\n" + "\n".join(batch_log))

            # Calcular y mostrar el tiempo total de ejecución hasta este batch
            elapsed_time = time.time() - start_time
            print(f"⏱ Tiempo de ejecución total hasta el batch #{batch_num}: {elapsed_time:.2f} segundos.")

            print(f"✅ Batch #{batch_num} completo: {len(applied)} sugerencias aplicadas.")
            batch_num += 1
            time.sleep(2)

        # 🔽 Crear resumen final
        with open("deepseek_suggestions_summary.md", "w") as f:
            f.write("# Resumen total de sugerencias aplicadas por DeepSeek\n\n")
            f.write("\n\n".join(summary_log))

        print(f"\n🎉 Proceso finalizado. Total de productos categorizados: {total_applied}")
        print("📄 Resumen generado en: deepseek_suggestions_summary.md")

    finally:
        session.close()

if __name__ == "__main__":
    main()
