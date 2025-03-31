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
    filename='scraper_errors_fravega.log',
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
# Insertar "Frávega" si no existe en la tabla retailers
retailer_name = "Fravega"
retailer_url = "https://www.fravega.com"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# URLs de las categorías
category_urls = [
    "https://www.fravega.com/l/tv-y-video/tv",
    "https://www.fravega.com/l/lavado",
    "https://www.fravega.com/l/celulares",
    "https://www.fravega.com/l/heladeras-freezers-y-cavas",
    "https://www.fravega.com/l/hogar",
    "https://www.fravega.com/l/informatica",
    "https://www.fravega.com/l/cocina",
    "https://www.fravega.com/l/muebles",
    "https://www.fravega.com/l/pequenos-electrodomesticos",
    "https://www.fravega.com/l/audio",
    "https://www.fravega.com/l/deportes-y-fitness",
    "https://www.fravega.com/l/climatizacion",
    "https://www.fravega.com/l/videojuegos"
]

# ─────────────────────────────────────────────────────────────
# Función para limpiar y convertir precios
def parse_price(price_str):
    if not price_str:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    category = base_url.split("/l/")[-1]
    while True:
        print(f"Scrapeando {category} - Página {page}...")
        try:
            driver.get(f"{base_url}/?page={page}")
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = soup.find_all("article", {"data-test-id": "result-item"})

            if not articles:
                print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                break

            for article in articles:
                try:
                    title = article.find("span", class_="sc-ca346929-0")
                    title_text = title.get_text(strip=True) if title else "Sin título"

                    price_block = article.find("div", {"data-test-id": "product-price"})
                    original_price_tag = price_block.find("span", class_="sc-66d25270-0") if price_block else None
                    final_price_tag = price_block.find("span", class_="sc-1d9b1d9e-0") if price_block else None

                    original_price = parse_price(original_price_tag.get_text(strip=True)) if original_price_tag else None
                    final_price = parse_price(final_price_tag.get_text(strip=True)) if final_price_tag else None

                    link_tag = article.find("a", href=True)
                    link = "https://www.fravega.com" + link_tag["href"] if link_tag else ""

                    img_tag = article.find("img")
                    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                    cursor.execute("""
                        INSERT INTO products (title, original_price, final_price, url, image, category, retailer_id, added_date, updated_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                    """, (
                        title_text,
                        original_price,
                        final_price,
                        link,
                        image_url,
                        category,
                        retailer_id
                    ))

                    print(f"✔ Producto: {title_text} | Final: {final_price} | Original: {original_price if original_price else 'N/A'}")
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
