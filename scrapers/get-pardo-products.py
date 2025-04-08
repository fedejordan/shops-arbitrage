import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# Logging
logging.basicConfig(
    filename='scraper_errors_pardo.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─────────────────────────────────────────────────────────────
# Variables de entorno y DB
load_dotenv()
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
retailer_name = "Pardo"
retailer_url = "https://www.pardo.com.ar"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))
cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# ─────────────────────────────────────────────────────────────
# Selenium config
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
driver = webdriver.Chrome(options=options)

# ─────────────────────────────────────────────────────────────
# Precios como float
def parse_price(price_str):
    if not price_str:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

# ─────────────────────────────────────────────────────────────
# Funciones auxiliares
def perform_advanced_scroll(max_attempts=5, wait_time=1):
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {total_height * i / 10});")
        time.sleep(0.3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(wait_time)
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Ver más') or contains(text(), 'Cargar más')]")
        for button in buttons:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(wait_time)
    except Exception as e:
        logging.warning(f"No se encontró botón de 'Ver más': {e}")
    for _ in range(max_attempts):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)

# ─────────────────────────────────────────────────────────────
# URLs
category_urls = [
    "https://www.pardo.com.ar/tv-y-video",
    "https://www.pardo.com.ar/rodados",
    "https://www.pardo.com.ar/bebes-y-ninos",
    "https://www.pardo.com.ar/equipaje",
    "https://www.pardo.com.ar/indumentaria-y-accesorios",
    "https://www.pardo.com.ar/audio",
    "https://www.pardo.com.ar/telefon%C3%ADa",
    "https://www.pardo.com.ar/informatica",
    "https://www.pardo.com.ar/electrodomesticos",
    "https://www.pardo.com.ar/climatizacion",
    "https://www.pardo.com.ar/hogar",
    "https://www.pardo.com.ar/jardin",
    "https://www.pardo.com.ar/belleza-y-salud"
]

for category_url in category_urls:
    print(f"\nProcesando categoría: {category_url}")
    page = 1
    while True:
        try:
            driver.get(f"{category_url}/?page={page}")
            time.sleep(3)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.vtex-search-result-3-x-galleryItem"))
            )
            perform_advanced_scroll()

            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.select("div.vtex-search-result-3-x-galleryItem")
            if not products or len(products) < 8:
                print("Fin de categoría.")
                break

            for product in products:
                try:
                    section = product.find("section", class_="vtex-product-summary-2-x-container")
                    if not section:
                        continue

                    title_tag = section.find("h3") or section.find("span", class_="vtex-product-summary-2-x-productBrand")
                    title = title_tag.get_text(strip=True) if title_tag else ""

                    a_tag = section.find("a", href=True)
                    link = "https://www.pardo.com.ar" + a_tag["href"] if a_tag else ""

                    img_tag = section.find("img")
                    image_url = img_tag["src"] if img_tag else ""

                    final_price = section.find(class_=lambda x: x and "sellingPrice" in x)
                    final_price_str = final_price.get_text(strip=True) if final_price else ""

                    original_price = section.find(class_=lambda x: x and "listPrice" in x)
                    original_price_str = original_price.get_text(strip=True) if original_price else ""

                    category = category_url.replace("https://www.pardo.com.ar/", "").strip("/")

                    # Precios convertidos
                    original_price_f = parse_price(original_price_str)
                    final_price_f = parse_price(final_price_str)

                    if not title or not link:
                        continue

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
                    """, (title, original_price_f, final_price_f, link, image_url, category, retailer_id))

                    print(f"✔ Producto: {title} - {final_price_f}")
                except Exception as e:
                    logging.error(f"🛑 Error procesando producto: {e}")
                    continue

            conn.commit()
            print(f"💾 Página {page} de {category} guardada.")
            page += 1
        except Exception as e:
            logging.error(f"🔥 Error en página {page} de {category_url}: {e}")
            break

# Cierre
driver.quit()
cursor.close()
conn.close()
print("\n✅ Scrapeo completo.")
