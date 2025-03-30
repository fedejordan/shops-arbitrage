from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv
import logging

# ─────────────────────────────────────────────────────────────
# Configuración del log de errores
logging.basicConfig(
    filename='scraper_errors.log',
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

# URLs de categorías
category_urls = [
    "https://www.cetrogar.com.ar/tecnologia.html",
    "https://www.cetrogar.com.ar/electrodomesticos.html",
    "https://www.cetrogar.com.ar/bazar-y-decoracion.html",
    "https://www.cetrogar.com.ar/belleza-y-cuidado-personal.html",
    "https://www.cetrogar.com.ar/hogar.html",
    "https://www.cetrogar.com.ar/herramientas.html",
    "https://www.cetrogar.com.ar/deportes-y-fitness.html",
    "https://www.cetrogar.com.ar/bebes-y-ninos.html",
    "https://www.cetrogar.com.ar/otras-categorias.html"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    category = base_url.split("/")[-1].replace(".html", "")
    while True:
        print(f"Scrapeando {category} - Página {page}...")
        try:
            driver.get(f"{base_url}?p={page}")
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.find_all("li", class_="item product product-item images-deferred")

            if not products:
                print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                break

            for product in products:
                try:
                    title_tag = product.find("div", class_="product name product-item-name")
                    title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                    link_tag = product.find("a", class_="product-item-info product-card", href=True)
                    link = link_tag["href"] if link_tag else ""

                    img_tag = product.find("img", class_="product-image-photo")
                    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                    price_box = product.find("div", class_="price-box price-final_price")
                    original_price = ""
                    final_price = ""
                    if price_box:
                        discount_span = price_box.find("span", class_="special-price")
                        if discount_span:
                            old_price_container = price_box.find("span", class_="old-price")
                            if old_price_container:
                                original_price_elem = old_price_container.find("span", class_="price")
                                original_price = original_price_elem.get_text(strip=True) if original_price_elem else ""
                            final_price_elem = discount_span.find("span", class_="price")
                            final_price = final_price_elem.get_text(strip=True) if final_price_elem else ""
                        else:
                            final_price_elem = price_box.find("span", id=lambda x: x and x.startswith("product-price-"))
                            if not final_price_elem:
                                price_spans = price_box.find_all("span", class_="price")
                                if price_spans:
                                    final_price = price_spans[-1].get_text(strip=True)
                            else:
                                final_price = final_price_elem.get_text(strip=True)

                    cursor.execute("""
                        INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                    """, (
                        title,
                        original_price,
                        final_price,
                        link,
                        image_url,
                        category
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
