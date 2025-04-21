from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv
import logging
import re
import html

# ─────────────────────────────────────────────────────────────
# Configuración del log de errores
logging.basicConfig(
    filename='scraper_errors_naldo.log',
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

# Insertar retailer si no existe
retailer_name = "Naldo"
retailer_url = "https://www.naldo.com.ar"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))
cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Función para limpiar precios
def parse_price(price_str):
    if not price_str or price_str == "N/A":
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# ─────────────────────────────────────────────────────────────
# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

category_urls = [
    "https://www.naldo.com.ar/celulares/",
    "https://www.naldo.com.ar/tv-audio-y-video",
    "https://www.naldo.com.ar/climatizacion",
    "https://www.naldo.com.ar/electrodomesticos",
    "https://www.naldo.com.ar/tecnologia",
    "https://www.naldo.com.ar/salud-belleza-y-fitness",
    "https://www.naldo.com.ar/hogar-jardin-y-tiempo-libre",
    "https://www.naldo.com.ar/rodados"
]

start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        try:
            driver.get(f"{base_url}?page={page}")
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.select("div.naldoar-search-result-3-x-galleryItem")

            if not products:
                print("🚫 No se encontraron productos en esta página. Fin de categoría.")
                break

            for product in products:
                try:
                    title_tag = product.find("span", class_="vtex-product-summary-2-x-productBrand")
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    title = html.escape(title)

                    final_price_tag = product.select_one("span.vtex-product-price-1-x-sellingPriceValue")
                    final_price = final_price_tag.get_text(strip=True) if final_price_tag else ""
                    
                    original_price_tag = product.select_one("span.vtex-product-price-1-x-listPriceValue")
                    original_price = original_price_tag.get_text(strip=True) if original_price_tag else ""

                    a_tag = product.find("a", class_="vtex-product-summary-2-x-clearLink")
                    link = "https://www.naldo.com.ar" + a_tag["href"] if a_tag and "href" in a_tag.attrs else ""

                    img_tag = product.find("img", class_="vtex-product-summary-2-x-image")
                    image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                    parts = base_url.strip("/").split("/")
                    category = parts[-1] if parts else "N/A"

                    parsed_original = parse_price(original_price)
                    parsed_final = parse_price(final_price)

                    print(f"Producto: {title} | Final: {parsed_final} | Original: {parsed_original if parsed_original else 'N/A'}")

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
                        parsed_original,
                        parsed_final,
                        link,
                        image_url,
                        category,
                        retailer_id
                    ))

                    print(f"✔ Producto: {title} | Final: {parsed_final} | Original: {parsed_original if parsed_original else 'N/A'}")
                except Exception as e:
                    logging.error(f"🛑 Error procesando producto en {base_url} página {page}: {e}")
                    continue

            conn.commit()
            print(f"💾 Página {page} guardada.\n")
            page += 1
        except Exception as e:
            logging.error(f"🔥 Error al cargar página {page} de {base_url}: {e}")
            break

# Finalización
driver.quit()
cursor.close()
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time
print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
