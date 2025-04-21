from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    filename='scraper_errors_samsung.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─────────────────────────────────────────────────────────────
# Cargar variables de entorno desde .env
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
# Insertar "Samsung Argentina" si no existe en la tabla retailers
retailer_name = "Samsung Argentina"
retailer_url = "https://www.samsung.com/ar"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────────────────────────
# Lista de URLs de categorías
category_urls = [
    "https://www.samsung.com/ar/tvs/all-tvs/",
    "https://www.samsung.com/ar/audio-devices/all-audio-devices/",
    "https://www.samsung.com/ar/projectors/all-projectors/",
    "https://www.samsung.com/ar/refrigerators/all-refrigerators/",
    "https://www.samsung.com/ar/washers-and-dryers/all-washers-and-dryers/",
    "https://www.samsung.com/ar/vacuum-cleaners/all-vacuum-cleaners/",
    "https://www.samsung.com/ar/dishwashers/",
    "https://www.samsung.com/ar/cooking-appliances/all-cooking-appliances/",
    "https://www.samsung.com/ar/air-conditioners/all-air-conditioners/",
    "https://www.samsung.com/ar/computers/all-computers/",
    "https://www.samsung.com/ar/monitors/all-monitors/",
    "https://www.samsung.com/ar/mobile-accessories/all-mobile-accessories/",
    "https://www.samsung.com/ar/smartphones/all-smartphones/",
]

# ─────────────────────────────────────────────────────────────
# Función para limpiar y convertir precios
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
# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    print(f"Scrapeando categoría: {base_url}")
    driver.get(base_url)
    time.sleep(3)

    while True:
        try:
            ver_mas_btn = driver.find_element(By.CSS_SELECTOR, "button.pd19-product-finder__view-more-btn")
            if ver_mas_btn.is_displayed():
                print("🔄 Clic en 'Ver más' para cargar más productos...")
                driver.execute_script("arguments[0].click();", ver_mas_btn)
                time.sleep(3)
            else:
                break
        except Exception:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select("div.pd19-product-card__item")
    print(f"🧾 Se encontraron {len(products)} productos.")

    url_parts = base_url.rstrip("/").split("/")
    category = url_parts[-1] if url_parts[-1] != "" else url_parts[-2]

    for product in products:
        try:
            title_tag = product.find("a", class_="pd19-product-card__name")
            title = title_tag.get_text(strip=True) if title_tag else "Sin título"
            title = html.escape(title)
            
            link = "https://www.samsung.com" + title_tag["href"] if title_tag and "href" in title_tag.attrs else ""

            price_tag = product.find("strong", class_="pd19-product-card__current-price")
            final_price_str = price_tag.get_text(strip=True) if price_tag else ""
            final_price = parse_price(final_price_str)

            original_price = None  # Samsung no muestra precio original en su web por ahora

            img_tag = product.select_one("a.pd19-product-card__img img.image__main")
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
            """, (title, original_price, final_price, link, image_url, category, retailer_id))

            conn.commit()
            print(f"✔ Producto: {title} | Final: {final_price} | Link: {link}")

        except Exception as e:
            logging.error(f"🛑 Error procesando producto en {category}: {e}")
            continue

# ─────────────────────────────────────────────────────────────
# Cierre
driver.quit()
cursor.close()
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time

print("\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")
