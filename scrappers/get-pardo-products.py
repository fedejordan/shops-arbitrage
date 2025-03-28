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

# Configuración de Selenium con tamaño de ventana forzado
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("window-size=1920,1080")
driver = webdriver.Chrome(options=options)

# URL de la categoría (ejemplo)
category_url = "https://www.pardo.com.ar/tv-y-video/"

driver.get(category_url)
time.sleep(3)

while True:
    try:
        # Espera y obtiene el span con la cuenta de productos
        count_elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.vtex-search-result-3-x-showingProductsCount"))
        )
        count_text = count_elem.text.strip()  # Ej: "20 de 63" o "63"
        if " de " in count_text:
            current_str, total_str = count_text.split(" de ")
            current_count = int(current_str)
            total_count = int(total_str)
        else:
            current_count = int(count_text)
            total_count = current_count
        print(f"Mostrando {current_count} de {total_count}")

        # Si ya se cargaron todos, salimos del loop
        if current_count >= total_count:
            print("Todos los productos cargados.")
            break

        # Intentar hacer clic en el botón "Mostrar más"
        mostrar_mas_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(),'Mostrar más')]]"))
        )
        mostrar_mas_btn.click()
        print("Clic en 'Mostrar más'...")
    except Exception as e:
        print("No se encontró el botón 'Mostrar más' o se produjo un error:", e)
        break
    time.sleep(3)

# Hacemos un último scroll para asegurarnos que se hayan cargado todos los items
try:
    container = driver.find_element(By.ID, "gallery-layout-container")
    last_height = driver.execute_script("return arguments[0].scrollHeight;", container)
    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", container)
        time.sleep(2)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", container)
        if new_height == last_height:
            break
        last_height = new_height
except Exception as e:
    print("No se pudo hacer scroll en el contenedor:", e)

# Ahora obtenemos los elementos de producto usando Selenium
product_elements = driver.find_elements(By.CSS_SELECTOR, "div.vtex-search-result-3-x-galleryItem")
print(f"Se encontraron {len(product_elements)} productos en total.")

# Para extraer datos, usamos BeautifulSoup sobre el outerHTML de cada elemento
for elem in product_elements:
    try:
        soup_item = BeautifulSoup(elem.get_attribute("outerHTML"), "html.parser")
        section = soup_item.find("section", class_="vtex-product-summary-2-x-container")
        if not section:
            continue

        title_tag = section.find("h3", class_="vtex-product-summary-2-x-productNameContainer")
        title = title_tag.get_text(strip=True) if title_tag else section.get("aria-label", "").strip()
        
        a_tag = section.find("a", href=True)
        link = "https://www.pardo.com.ar" + a_tag["href"] if a_tag else ""
        
        img_tag = section.find("img")
        image_url = img_tag["src"] if img_tag and img_tag.get("src") else ""
        
        final_price_tag = section.find("span", class_="vtex-product-price-1-x-sellingPriceValue--summary")
        final_price = final_price_tag.get_text(strip=True) if final_price_tag else ""
        
        original_price_tag = section.find("span", class_="vtex-product-price-1-x-listPriceValue--summary")
        original_price = original_price_tag.get_text(strip=True) if original_price_tag else ""
        
        category = category_url.replace("https://www.pardo.com.ar/", "").strip("/")
        
        cursor.execute("""
            INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
        """, (title, original_price, final_price, link, image_url, category))
        
        print(f"Producto: {title} - {final_price}")
    except Exception as e:
        print("Error al procesar un producto:", e)
        continue

driver.quit()
conn.commit()
cursor.close()
conn.close()

print("\nScrapeo completo.")
