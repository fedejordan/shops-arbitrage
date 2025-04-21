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
    filename='scraper_errors_oncity.log',
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

# URL de categorías
category_urls = [
    "https://www.oncity.com/aire-libre",
    "https://www.oncity.com/audio-tv-y-video",
    "https://www.oncity.com/arte-libreria-y-merceria",
    "https://www.oncity.com/bebes",
    "https://www.oncity.com/belleza-y-cuidado-personal",
    "https://www.oncity.com/compra-internacional",
    "https://www.oncity.com/deportes-y-fitness",
    "https://www.oncity.com/electrodomesticos",
    "https://www.oncity.com/herramientas-y-construccion",
    "https://www.oncity.com/hogar",
    "https://www.oncity.com/iluminacion",
    "https://www.oncity.com/juegos-y-juguetes",
    "https://www.oncity.com/mascotas",
    "https://www.oncity.com/muebles",
    "https://www.oncity.com/salud-y-equipamiento-medico",
    "https://www.oncity.com/tecnologia",
    "https://www.oncity.com/tiempo-libre",
    "https://www.oncity.com/Autos-y-Motos",
]

# ─────────────────────────────────────────────────────────────
# Insertar "OnCity" si no existe en la tabla retailers
retailer_name = "OnCity"
retailer_url = "https://www.oncity.com"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Función para limpiar y convertir precios
def parse_price(price_str):
    if not price_str or price_str in ["N/A", ""]:
        return None
    try:
        cleaned = re.sub(r"[^\d,\.]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# ─────────────────────────────────────────────────────────────
# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    category = base_url.split("/")[-1]
    while True:
        print(f"Scrapeando {category} - Página {page}...")
        try:
            driver.get(f"{base_url}?page={page}")
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.select("div.vtex-search-result-3-x-galleryItem")

            if not products:
                print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                break

            for product in products:
                try:
                    title_tag = product.find("span", class_="vtex-product-summary-2-x-productBrand")
                    title = title_tag.get_text(strip=True) if title_tag else "Sin título"
                    title = html.escape(title)

                    final_price_container = product.find("span", class_="vtex-product-price-1-x-sellingPrice")
                    final_price_str = final_price_container.get_text(strip=True) if final_price_container else ""
                    final_price = parse_price(final_price_str)

                    original_price_container = product.find("span", class_="vtex-product-price-1-x-listPrice")
                    original_price_str = original_price_container.get_text(strip=True) if original_price_container else ""
                    original_price = parse_price(original_price_str)

                    a_tag = product.find("a", class_="vtex-product-summary-2-x-clearLink")
                    link = "https://www.oncity.com" + a_tag["href"] if a_tag and "href" in a_tag.attrs else ""

                    img_tag = product.find("img", class_="vtex-product-summary-2-x-imageNormal")
                    image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                    print(f"🛒 Procesando producto: {title}")

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
                    logging.error(f"🛑 Error procesando producto en {category} página {page}: {e}")
                    continue

            conn.commit()
            print(f"💾 Página {page} de {category} guardada.\n")
            page += 1

        except Exception as e:
            logging.error(f"🔥 Error al cargar página {page} de {category}: {e}")
            break

# Cierre
driver.quit()
cursor.close()
conn.close()

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
