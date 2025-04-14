import os
import time
import html
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, Retailer
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BATCH_SIZE = 10

RETAILER_SELECTORS = {
    "garbarino.com": "div.product-page__description-content",
    "fravega.com": "div.sc-34c797d0-5",
    "cetrogar.com.ar": [
        "div.product.attribute.description",
        "div.destacada-txt-content"
    ],
    "megatone.net": "div.Descripcion.DescripcionAmpliada article",
    "musimundo.com": "div#accordion-details",
    "naldo.com.ar": "div.naldoar-store-component-1-x-productDescriptionText",
    "novogar.com.ar": "div.fichaProducto_especificaciones_contenido",
    "oncity.com.ar": "div.vtex-store-components-3-x-content.h-auto",
    "pardo.com.ar": "div.vtex-store-components-3-x-content",
    "philco.com.ar": "div[data-content-type='text'][data-element='main']",
    "samsung.com/ar": "__custom_samsung__",
    "whirlpool.com.ar": "__custom_whirlpool__",
}

def extract_whirlpool_description(soup):
    specs = soup.select("div.technical-table--item")
    pairs = []
    for item in specs:
        key = item.find("h3")
        value = item.find("span")
        if key and value:
            pairs.append(f"{key.get_text(strip=True)}: {value.get_text(strip=True)}")
    return " | ".join(pairs)[:2000]

def extract_samsung_description(soup):
    benefit_blocks = soup.select("div.benefit-content-container div.benefit-content")
    texts = []
    for block in benefit_blocks:
        heading = block.find("h3")
        para = block.find("p")
        if heading:
            texts.append(heading.get_text(strip=True))
        if para:
            texts.append(para.get_text(strip=True))
    return " ".join(texts).strip()[:2000]

def get_clean_text_from_url(url):
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        domain = httpx.URL(url).host or ""
        print(f"🌐 Dominio detectado: {domain}")

        selected_text = ""

        for site, selector in RETAILER_SELECTORS.items():
            if site in domain:
                if selector == "__custom_samsung__":
                    return extract_samsung_description(soup)
                elif selector == "__custom_whirlpool__":
                    return extract_whirlpool_description(soup)

                if isinstance(selector, list):
                    selected_text = " ".join(
                        el.get_text(separator=" ", strip=True)
                        for sel in selector
                        for el in soup.select(sel)
                    )
                else:
                    el = soup.select_one(selector)
                    if el:
                        selected_text = el.get_text(separator=" ", strip=True)

                selected_text = html.unescape(selected_text)
                selected_text = " ".join(selected_text.split())
                print(f"🎯 Selector personalizado aplicado para {site}")
                break

        if not selected_text:
            fallback = soup.body.get_text(separator=" ", strip=True) if soup.body else soup.get_text()
            selected_text = " ".join(html.unescape(fallback).split())
            print("⚠️ Usando fallback al texto completo")

        return selected_text[:2000]

    except Exception as e:
        print(f"⚠️ Error obteniendo HTML de {url}: {e}")
        return ""

def build_prompt(product, page_content):
    retailer_name = product.retailer.name if product.retailer else "Desconocido"
    return (
        f"Descripción de producto para ecommerce.\n\n"
        f"Título: {product.title}\n"
        f"Precio: ${int(product.final_price or 0)}\n"
        f"Retailer: {retailer_name}\n"
        f"Contenido de la página del producto:\n\n"
        f"{page_content}\n\n"
        f"Generá una descripción breve, clara, vendedora y sin repetir el título."
    )

def get_deepseek_description(prompt):
    try:
        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Sos un copywriter experto en ecommerce."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=20.0
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("❌ DeepSeek falló:", e)
        return None

def get_products_missing_ai_description(session):
    return (
        session.query(Product)
        .filter(Product.ai_description == None)
        .order_by(Product.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )

def main():
    session = SessionLocal()
    total_completed = 0
    batch_num = 1

    try:
        while True:
            print(f"\n🚀 Procesando batch #{batch_num}...")
            products = get_products_missing_ai_description(session)
            if not products:
                print("✅ No quedan más productos sin descripción.")
                break

            for product in products:
                print(f"🔎 Generando descripción para: {product.title}")
                product.retailer = session.query(Retailer).get(product.retailer_id)

                page_content = get_clean_text_from_url(product.url)
                prompt = build_prompt(product, page_content)
                description = get_deepseek_description(prompt)

                if description:
                    product.ai_description = description
                    print(f"✅ Descripción generada y asignada.")
                    total_completed += 1
                else:
                    print(f"⚠️ No se pudo generar descripción para: {product.title}")

            session.commit()
            print(f"✅ Batch #{batch_num} completo.")
            batch_num += 1
            time.sleep(1)

    finally:
        session.close()
        print(f"\n🎉 Proceso finalizado. Total de productos actualizados: {total_completed}")

if __name__ == "__main__":
    main()
