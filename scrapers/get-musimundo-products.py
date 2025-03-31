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
    filename='scraper_errors_musimundo.log',
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

# ─────────────────────────────────────────────────────────────
# Insertar retailer Musimundo si no existe
retailer_name = "Musimundo"
retailer_url = "https://www.musimundo.com"

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
    if not price_str:
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
options.add_argument("window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
})

# ─────────────────────────────────────────────────────────────
# URLs a scrapear
category_urls = [
    "https://www.musimundo.com/climatizacion/c/2",
    "https://www.musimundo.com/audio-tv-video/c/3",
    "https://www.musimundo.com/electrohogar/c/7",
    "https://www.musimundo.com/telefonia/c/5",
    "https://www.musimundo.com/informatica/c/6",
    "https://www.musimundo.com/pequenos/c/8",
    "https://www.musimundo.com/gaming/c/1",
    "https://www.musimundo.com/cuidado-personal-y-salud/c/164",
    "https://www.musimundo.com/hogar-y-aire-libre/c/10",
    "https://www.musimundo.com/ninos/c/15",
    "https://www.musimundo.com/camaras/c/4",
    "https://www.musimundo.com/rodados/c/9",
    "https://www.musimundo.com/audio-tv-video/accesorios-de-imagen-y-sonido/c/62",
    "https://www.musimundo.com/mas-categorias/c/701"
]

# ─────────────────────────────────────────────────────────────
start_time = time.time()

for base_url in category_urls:
    print(f"🧭 Cargando categoría: {base_url}")
    try:
        driver.get(base_url)
        time.sleep(5)

        scroll_pause_time = 5
        last_height = driver.execute_script("return document.body.scrollHeight")
        max_loops = 20
        loops = 0

        while loops < max_loops:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            loops += 1

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.product-card")
        print(f"📦 Productos encontrados: {len(products)}")

        if not products:
            print(f"🚫 Sin productos en: {base_url}")
            continue

        url_parts = base_url.split("/")
        category = url_parts[3] if len(url_parts) > 3 else "N/A"

        for product in products:
            try:
                title_tag = product.select_one("div.product-card_name")
                title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                price_container = product.select_one("div.mus-pro-price")
                final_price_str = None
                if price_container:
                    price_tag = price_container.find("span", {"data-test-item-price": True})
                    if price_tag:
                        price_value_tag = price_tag.find("span")
                        final_price_str = price_value_tag.get_text(strip=True) if price_value_tag else ""

                original_price = None  # No disponible por ahora
                final_price = parse_price(final_price_str)

                a_tag = product.find("a", class_="mus-pro-thumb")
                link = "https://www.musimundo.com" + a_tag["href"] if a_tag and "href" in a_tag.attrs else ""

                img_tag = product.find("img")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, retailer_id, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (title, original_price, final_price, link, image_url, category, retailer_id))

                print(f"✔ Producto: {title} | Final: {final_price}")

            except Exception as e:
                logging.error(f"🛑 Error procesando producto en {category}: {e}")
                continue

        conn.commit()
        print(f"💾 Categoría {category} guardada.\n")

    except Exception as e:
        logging.error(f"🔥 Error al procesar página: {base_url} - {e}")
        continue

# ─────────────────────────────────────────────────────────────
driver.quit()
cursor.close()
conn.close()

end_time = time.time()
print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {end_time - start_time:.2f} segundos.")
