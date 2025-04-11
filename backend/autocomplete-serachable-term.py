import os
import re
import time
import unicodedata
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product

BATCH_SIZE = 50

MODEL_REGEX = re.compile(r"\b[A-Z]{2,}-?\d+[A-Z0-9\-]*\b")
GENERIC_TERMS = {"PS4", "PS5", "XBOX", "TV", "LED", "UHD", "FULLHD", "HD", "4K", "WI-FI"}

def normalize_for_searchable_term(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf-8")  # elimina tildes
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", "", text)  # elimina símbolos, deja letras, números, guiones
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = " ".join(text.split())
    return text

def extract_model_with_regex(title: str) -> str | None:
    matches = MODEL_REGEX.findall(title.upper())
    for match in matches:
        if match.upper() not in GENERIC_TERMS:
            return match
    return None

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

            for product in products:
                model = extract_model_with_regex(product.title)
                if model:
                    print(f"🔧 {product.title} → (regex) → {model}")
                else:
                    model = normalize_for_searchable_term(product.title)
                    print(f"🔧 {product.title} → (full title) → {model}")
                product.searchable_term = model
                total_applied += 1

            session.commit()
            print(f"✅ Batch #{batch_num} completo. Productos procesados: {len(products)}")
            batch_num += 1
            time.sleep(1)

        elapsed_time = time.time() - start_time
        print(f"\n🎉 Proceso finalizado. Total completados: {total_applied}")
        print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos")

    finally:
        session.close()

if __name__ == "__main__":
    main()
