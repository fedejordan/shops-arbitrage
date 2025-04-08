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
    filename='scraper_errors_novogar.log',
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
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────────────────────────
# Insertar "Novogar" si no existe en la tabla retailers
retailer_name = "Novogar"
retailer_url = "https://www.novogar.com.ar"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))
conn.commit()

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Función para limpiar y convertir precios
def parse_price(price_str):
    if not price_str or price_str in ["N/A", ""]:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# ─────────────────────────────────────────────────────────────
# Función para hacer scroll y cargar todos los productos
def scroll_to_load_all_products(driver, max_scrolls=30):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
        last_height = new_height
        scroll_count += 1

# ─────────────────────────────────────────────────────────────
# Categorías
category_urls = [
    "https://www.novogar.com.ar/categorias/agua-caliente",
    "https://www.novogar.com.ar/categorias/aire-acondicionado",
    "https://www.novogar.com.ar/categorias/audio-y-video",
    "https://www.novogar.com.ar/categorias/bicicletas",
    "https://www.novogar.com.ar/categorias/calefaccion-",
    "https://www.novogar.com.ar/categorias/cocinas",
    "https://www.novogar.com.ar/categorias/colchones-y-sommier",
    "https://www.novogar.com.ar/categorias/cuidado-personal",
    "https://www.novogar.com.ar/categorias/electrodomesticos",
    "https://www.novogar.com.ar/categorias/fitness",
    "https://www.novogar.com.ar/categorias/gamer",
    "https://www.novogar.com.ar/categorias/heladeras",
    "https://www.novogar.com.ar/categorias/herramientas",
    "https://www.novogar.com.ar/categorias/informatica",
    "https://www.novogar.com.ar/categorias/jardin",
    "https://www.novogar.com.ar/categorias/lavado",
    "https://www.novogar.com.ar/categorias/limpieza-y-hogar",
    "https://www.novogar.com.ar/categorias/luces",
    "https://www.novogar.com.ar/categorias/muebles",
    "https://www.novogar.com.ar/categorias/seguridad-para-el-hogar",
    "https://www.novogar.com.ar/categorias/telefonia",
    "https://www.novogar.com.ar/categorias/television-",
    "https://www.novogar.com.ar/categorias/ventilacion"

]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    category = base_url.split("/")[-1]
    print(f"\nScrapeando {category}...")

    try:
        driver.get(base_url)
        time.sleep(3)
        scroll_to_load_all_products(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.one-product")

        if not products:
            print("🚫 No se encontraron productos.")
            continue

        for product in products:
            try:
                title_tag = product.select_one("h3.product-card__name")
                title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                a_tag = product.select_one("div.product-card a")
                link = "https://www.novogar.com.ar" + a_tag["href"] if a_tag and "href" in a_tag.attrs else ""

                price_tag = product.select_one("p.frase_precio.cat-mobile-precioof") or \
                            product.select_one("div.productCard_prices p.productCard_price_regular")
                final_price = parse_price(price_tag.get_text(strip=True)) if price_tag else None

                original_price_tag = product.select_one("p.productCard_price_regular:has(~ p.productCard_price_discount)")
                original_price = parse_price(original_price_tag.get_text(strip=True)) if original_price_tag else final_price

                img_tags = product.select("div.productCard_img img")
                if img_tags:
                    image_url = img_tags[-1]["src"]
                    if image_url.startswith("/"):
                        image_url = "https://www.novogar.com.ar" + image_url
                else:
                    image_url = ""

                print(f"🔍 Procesando producto: {title} | URL: {link}")

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
                """, (title, original_price, final_price, link, image_url, category, retailer_id))

                print(f"✔ Producto: {title} | Final: {final_price} | Original: {original_price if original_price else 'N/A'}")

            except Exception as e:
                logging.error(f"🛑 Error procesando producto en {category}: {e}")
                continue

        conn.commit()
        print(f"💾 Categoría {category} guardada.\n")

    except Exception as e:
        logging.error(f"🔥 Error en categoría {category}: {e}")
        continue

# Cierre
driver.quit()
cursor.close()
conn.close()

# Tiempo total
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
