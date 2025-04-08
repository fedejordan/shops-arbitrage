from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv
import logging
import re

# ─────────────────────────────────────────────────────────────
# Configuración del log de errores
logging.basicConfig(
    filename='scraper_errors_philco.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─────────────────────────────────────────────────────────────
# Cargar variables desde .env
load_dotenv()

# Conexión a PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DBNAME"),
    user=os.getenv("DBUSER"),
    password=os.getenv("DBPASSWORD"),
    host=os.getenv("DBHOST"),
    port=os.getenv("DBPORT")
)
cursor = conn.cursor()

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────────────────────────
# Insertar "Philco" si no existe en la tabla retailers
retailer_name = "Philco"
retailer_url = "https://philco.com.ar"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Función para parsear precios
def parse_price(price_str):
    if not price_str or price_str == "N/A":
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# URLs de categorías
categories_urls = [
    "https://philco.com.ar/tecnologia-y-accesorios.html",
    "https://philco.com.ar/salud-y-belleza.html",
    "https://philco.com.ar/herramientas/ver-todo-herramientas.html",
    "https://philco.com.ar/electrodomesticos/aspiradoras.html",
    "https://philco.com.ar/electrodomesticos/termotanque.html",
    "https://philco.com.ar/electrodomesticos/cocina.html",
    "https://philco.com.ar/electrodomesticos/lavado.html",
    "https://philco.com.ar/electrodomesticos/heladeras-y-freezers.html",
    "https://philco.com.ar/movilidad/ver-todo-movilidad.html",
    "https://philco.com.ar/audio/audio.html",
    "https://philco.com.ar/tv/ver-todo-tv.html",
    "https://philco.com.ar/aire-climatizacion/ver-todo-aire-y-climatizacion.html"
]

# Medir tiempo de inicio
start_time = time.time()

# Iterar sobre cada categoría
for category_url in categories_urls:
    category = category_url.split("/")[3] if len(category_url.split("/")) > 3 else "N/A"
    print(f"\nScrapeando categoría: {category_url} (Categoría: {category})...")

    try:
        driver.get(category_url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("ol.products.list.items.product-items li.item.product.product-item")

        if not products:
            print("🚫 No se encontraron productos.")
            continue

        for product in products:
            try:
                title_tag = product.select_one("h2.product.name.product-item-name a.product-item-link")
                title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                sku_tag = product.select_one("p.sku-producto")
                sku = sku_tag.get_text(strip=True) if sku_tag else "N/A"

                final_price_tag = product.select_one("div.price-box.price-final_price span.special-price span.price")
                final_price_str = final_price_tag.get_text(strip=True) if final_price_tag else "N/A"

                original_price_tag = product.select_one("div.price-box.price-final_price span.old-price span.price")
                original_price_str = original_price_tag.get_text(strip=True) if original_price_tag else "N/A"

                link_tag = product.select_one("h2.product.name.product-item-name a.product-item-link")
                link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "N/A"

                img_tag = product.select_one("img.product-image-photo")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                # 🔢 Conversión de precios
                original_price = parse_price(original_price_str)
                final_price = parse_price(final_price_str)

                print(f"Producto: {title} | SKU: {sku} | Final: {final_price} | Original: {original_price if original_price else 'N/A'}")

                # Verificar si el producto ya existe
                cursor.execute("""
                    SELECT id, original_price, final_price
                    FROM products
                    WHERE url = %s
                """, (link,))
                existing_product = cursor.fetchone()

                # Si existe y el precio cambió, guardar el histórico
                if existing_product:
                    product_id_db, old_original_price, old_final_price = existing_product
                    if (
                        (old_original_price != original_price and original_price is not None)
                        or (old_final_price != final_price and final_price is not None)
                    ):
                        cursor.execute("""
                            INSERT INTO historical_prices (product_id, original_price, final_price)
                            VALUES (%s, %s, %s)
                        """, (product_id_db, old_original_price, old_final_price))

                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, retail_category, retailer_id, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET 
                        title = EXCLUDED.title,
                        original_price = EXCLUDED.original_price,
                        final_price = EXCLUDED.final_price,
                        image = EXCLUDED.image,
                        retail_category = EXCLUDED.retail_category,
                        retailer_id = EXCLUDED.retailer_id,
                        updated_date = CURRENT_TIMESTAMP
                """, (
                    title,
                    original_price,
                    final_price,
                    link,
                    image_url,
                    category,
                    retailer_id
                ))

                print(f"✔ Producto: {title} | Final: {final_price} | Original: {original_price if original_price else 'N/A'}")

            except Exception as e:
                logging.error(f"🛑 Error procesando producto en {category_url}: {e}")
                continue

        conn.commit()
        print(f"💾 Productos de {category} guardados.\n")

    except Exception as e:
        logging.error(f"🔥 Error al procesar categoría {category_url}: {e}")
        continue

# Cierre
driver.quit()
cursor.close()
conn.close()

# Tiempo total
end_time = time.time()
elapsed_time = end_time - start_time

print("\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
