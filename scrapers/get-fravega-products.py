from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv
import logging
import re

# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    filename='scraper_errors_fravega.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DBNAME"),
    user=os.getenv("DBUSER"),
    password=os.getenv("DBPASSWORD"),
    host=os.getenv("DBHOST"),
    port=os.getenv("DBPORT")
)
cursor = conn.cursor()

# Configuración Selenium con user-agent
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────────────────────────
retailer_name = "Fravega"
retailer_url = "https://www.fravega.com"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

category_urls = [
    "https://www.fravega.com/l/articulos-de-libreria-y-papeleria/",
    "https://www.fravega.com/l/audio/",
    "https://www.fravega.com/l/bebes-y-primera-infancia/",
    "https://www.fravega.com/l/belleza-y-cuidado-corporal/",
    "https://www.fravega.com/l/camaras-y-video-camaras/",
    "https://www.fravega.com/l/camping-y-aire-libre/",
    "https://www.fravega.com/l/celulares/",
    "https://www.fravega.com/l/climatizacion/",
    "https://www.fravega.com/l/cocina/",
    "https://www.fravega.com/l/deportes-y-fitness/",
    "https://www.fravega.com/l/domotica/",
    "https://www.fravega.com/l/equipos-para-auto/",
    "https://www.fravega.com/l/heladeras-freezers-y-cavas/",
    "https://www.fravega.com/l/herramientas-y-construccion/griferias/",
    "https://www.fravega.com/l/herramientas-y-construccion/herramientas/",
    "https://www.fravega.com/l/herramientas-y-construccion/muebles-de-bano/",
    "https://www.fravega.com/l/herramientas-y-construccion/pintureria/",
    "https://www.fravega.com/l/herramientas-y-construccion/pisos-y-revestimientos,herramientas-y-construccion/ceramicos/",
    "https://www.fravega.com/l/herramientas-y-construccion/plomeria/",
    "https://www.fravega.com/l/herramientas-y-construccion/sanitarios/",
    "https://www.fravega.com/l/hogar/bano/",
    "https://www.fravega.com/l/hogar/bazar/",
    "https://www.fravega.com/l/hogar/colchones-y-sommiers/",
    "https://www.fravega.com/l/hogar/decoracion/",
    "https://www.fravega.com/l/hogar/ropa-de-cama/",
    "https://www.fravega.com/l/iluminacion/",
    "https://www.fravega.com/l/indumentaria/",
    "https://www.fravega.com/l/informatica/",
    "https://www.fravega.com/l/instrumentos-musicales/",
    "https://www.fravega.com/l/jardin/",
    "https://www.fravega.com/l/juguetes-y-juegos/juegos-de-aire-libre/",
    "https://www.fravega.com/l/juguetes-y-juegos/juegos-didacticos,bebes-y-primera-infancia/",
    "https://www.fravega.com/l/juguetes-y-juegos/juguetes-electronicos/",
    "https://www.fravega.com/l/juguetes-y-juegos/peluches-y-munecos-interactivos,juguetes-y-juegos/",
    "https://www.fravega.com/l/juguetes-y-juegos/rodados-para-ninos/",
    "https://www.fravega.com/l/juguetes-y-juegos/sets-y-otros/",
    "https://www.fravega.com/l/lavado/",
    "https://www.fravega.com/l/mascotas/",
    "https://www.fravega.com/l/muebles/",
    "https://www.fravega.com/l/pequenos-electrodomesticos/",
    "https://www.fravega.com/l/relojes/",
    "https://www.fravega.com/l/salud-y-bienestar/",
    "https://www.fravega.com/l/seguridad-para-el-hogar/",
    "https://www.fravega.com/l/termotanques-y-calefones/",
    "https://www.fravega.com/l/tv-y-video/",
    "https://www.fravega.com/l/videojuegos/",
]

def parse_price(price_str):
    if not price_str:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

start_time = time.time()

for base_url in category_urls:
    page = 1
    category = base_url.split("/l/")[-1].strip("/")
    while True:
        print(f"Scrapeando {category} - Página {page}...")
        try:
            full_url = f"{base_url}?page={page}"
            retries = 3
            articles = []

            while retries > 0:
                driver.get(full_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-test-id='result-item']"))
                    )
                except:
                    logging.warning(f"⏳ Timeout esperando artículos en {category} página {page}...")

                soup = BeautifulSoup(driver.page_source, "html.parser")
                articles = soup.find_all("article", {"data-test-id": "result-item"})

                if articles:
                    break
                else:
                    retries -= 1
                    if retries == 0:
                        print(driver.page_source[:500])
                        print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                        break
                    print(f"🔁 Reintentando página {page} de {category}...")

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

driver.quit()
cursor.close()
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time

print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
