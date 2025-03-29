from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv

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
    print(f"\nScrapeando categoría: {base_url}")
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

    # Extraer productos
    for product in products:
        try:
            title_tag = product.select_one("span.vtex-product-summary-2-x-brandName")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            original_price_tag = product.select_one("div.whirlpoolargio-store-theme-1-x-ListPrice")
            original_price = original_price_tag.get_text(strip=True).replace("$", "").replace("\xa0", "").replace(" ", "") if original_price_tag else "N/A"

            final_price_tag = product.select_one("div.whirlpoolargio-store-theme-1-x-SellingPrice span")
            final_price = final_price_tag.get_text(strip=True).replace("$", "").replace("\xa0", "").replace(" ", "") if final_price_tag else "N/A"

            image_tag = product.select_one("img.vtex-product-summary-2-x-imageNormal")
            image_url = image_tag["src"] if image_tag else ""

            a_tag = product.select_one("a.vtex-product-summary-2-x-clearLink")
            link = "https://www.whirlpool.com.ar" + a_tag["href"] if a_tag else "N/A"

            category = base_url.split("/")[-1]

            # Insertar en base
            cursor.execute("""
                INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
            """, (title, original_price, final_price, link, image_url, category))

            print(f"✓ {title} | Final: ${final_price} | Original: ${original_price}")

        except Exception as e:
            print("Error en producto:", e)

# Finalizar
driver.quit()
conn.commit()
cursor.close()
conn.close()
print("\nScrapeo completo.")
