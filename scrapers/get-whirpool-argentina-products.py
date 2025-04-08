from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
import re
from dotenv import load_dotenv
import logging

# ─────────────────────────────────────────────────────────────
# Logging
logging.basicConfig(
    filename='scraper_errors_whirlpool.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─────────────────────────────────────────────────────────────
# Cargar variables del entorno
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

# ─────────────────────────────────────────────────────────────
# Insertar retailer si no existe
retailer_name = "Whirlpool"
retailer_url = "https://www.whirlpool.com.ar"

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
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al parsear precio '{price_str}': {e}")
        return None

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Categorías Whirlpool
category_urls = [
    "https://www.whirlpool.com.ar/refrigeracion",
    "https://www.whirlpool.com.ar/lavado",
    "https://www.whirlpool.com.ar/coccion",
    "https://www.whirlpool.com.ar/empotrables",
    "https://www.whirlpool.com.ar/electrodomesticos",
    "https://www.whirlpool.com.ar/repuestos",
]

# Scrapeo
for base_url in category_urls:
    print(f"\n🔍 Scrapeando categoría: {base_url}")
    try:
        driver.get(base_url)
        time.sleep(4)

        previous_count = -1
        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.select("div.vtex-search-result-3-x-galleryItem")
            current_count = len(products)

            if current_count == previous_count:
                break  # No se cargaron más productos
            previous_count = current_count

            try:
                show_more = driver.find_element(By.XPATH, "//button[contains(., 'Mostrar más')]")
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(3)
            except Exception:
                break  # No hay botón, fin del paginado

        # Extraer productos cargados
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.vtex-search-result-3-x-galleryItem")

        for product in products:
            try:
                title_tag = product.select_one("span.vtex-product-summary-2-x-brandName")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                original_price_tag = product.select_one("div.whirlpoolargio-store-theme-1-x-ListPrice")
                original_price_str = original_price_tag.get_text(strip=True) if original_price_tag else ""

                final_price_tag = product.select_one("div.whirlpoolargio-store-theme-1-x-SellingPrice span")
                final_price_str = final_price_tag.get_text(strip=True) if final_price_tag else ""

                original_price = parse_price(original_price_str)
                final_price = parse_price(final_price_str)

                image_tag = product.select_one("img.vtex-product-summary-2-x-imageNormal")
                image_url = image_tag["src"] if image_tag else ""

                a_tag = product.select_one("a.vtex-product-summary-2-x-clearLink")
                link = "https://www.whirlpool.com.ar" + a_tag["href"] if a_tag else "N/A"

                category = base_url.split("/")[-1]

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

                conn.commit()
                print(f"✔ {title} | Final: ${final_price} | Original: ${original_price if original_price else 'N/A'}")
            except Exception as e:
                logging.error(f"🛑 Error procesando producto: {e}")
                continue

    except Exception as e:
        logging.error(f"🔥 Error en categoría {base_url}: {e}")
        continue

# Finalizar
driver.quit()
cursor.close()
conn.close()
print("\n✅ Scrapeo completo.")
