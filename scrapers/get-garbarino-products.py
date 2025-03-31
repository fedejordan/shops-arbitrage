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
    filename='scraper_errors_garbarino.log',
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

# Retailer info
retailer_name = "Garbarino"
retailer_url = "https://www.garbarino.com"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# Función para parsear precios
def parse_price(price_str):
    if not price_str or "N/A" in price_str:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# URLs de las categorías
category_urls = [
    "https://www.garbarino.com/celulares-notebooks-y-tecnologia",
    "https://www.garbarino.com/smart-tv-audio-y-video",
    "https://www.garbarino.com/electrodomesticos",
    "https://www.garbarino.com/salud-y-belleza",
    "https://www.garbarino.com/hogar-muebles-y-jardin",
    "https://www.garbarino.com/bebes-y-ninos",
    "https://www.garbarino.com/deportes-y-tiempo-libre",
    "https://www.garbarino.com/construccion",
    "https://www.garbarino.com/herramientas",
    "https://www.garbarino.com/animales-y-mascotas",
    "https://www.garbarino.com/moda-y-accesorios",
    "https://www.garbarino.com/arte-libreria-y-merceria",
    "https://www.garbarino.com/mas-categorias"
]

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
            products = soup.find_all("div", class_="product-card-design6-vertical-wrapper")

            if not products:
                print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                break

            for product in products:
                try:
                    title_tag = product.find("div", class_="product-card-design6-vertical__name")
                    title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                    final_price_container = product.select_one("div.product-card-design6-vertical__price")
                    final_price_str = ""
                    if final_price_container:
                        spans = final_price_container.find_all("span")
                        final_price_str = spans[-1].get_text(strip=True) if spans else ""

                    original_price_container = product.select_one("div.product-card-design6-vertical__prev-price")
                    original_price_str = ""
                    if original_price_container:
                        orig_price_div = original_price_container.select_one("div.text-no-wrap.grey--text")
                        if orig_price_div:
                            orig_spans = orig_price_div.find_all("span")
                            original_price_str = orig_spans[-1].get_text(strip=True) if orig_spans else ""

                    link_tag = product.find("a", class_="card-anchor")
                    link = "https://www.garbarino.com" + link_tag["href"] if link_tag and "href" in link_tag.attrs else ""

                    img_tag = product.find("img", class_="ratio-image__image")
                    image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                    # Parsear precios
                    original_price = parse_price(original_price_str)
                    final_price = parse_price(final_price_str)

                    cursor.execute("""
                        INSERT INTO products (title, original_price, final_price, url, image, category, retailer_id, added_date, updated_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
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

# Cierre de Selenium y PostgreSQL
driver.quit()
cursor.close()
conn.close()

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
