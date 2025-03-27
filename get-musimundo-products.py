from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv
import re

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

# Configuración de Selenium con opciones para evitar detección en modo headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# Establecer un tamaño de ventana grande
options.add_argument("window-size=1920,1080")
# Cambiar el user-agent para que parezca un navegador normal
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
# Desactivar la bandera que indica que estamos en modo automatizado
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
# Ejecutar script para ocultar la propiedad webdriver
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """
})

print("Cargando página...")
base_url = "https://www.musimundo.com/climatizacion/c/2"
driver.get(base_url)
time.sleep(5)
print("Página cargada.")

# Scroll dinámico: se hace scroll hasta que la altura de la página no cambie
scroll_pause_time = 5
last_height = driver.execute_script("return document.body.scrollHeight")
max_loops = 20  # evitar loops infinitos
loops = 0

while loops < max_loops:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Scroll {loops+1}: altura actual = {new_height}")
    if new_height == last_height:
        break
    last_height = new_height
    loops += 1

# Parseo del contenido cargado
soup = BeautifulSoup(driver.page_source, "html.parser")
products = soup.select("div.product-card")
print(f"Productos cargados: {len(products)}")

if not products:
    print("No se encontraron productos. Verifica si la estructura de la página o el selector ha cambiado.")

# Iterar sobre cada producto y extraer datos
for product in products:
    try:
        # Extraer título: se busca en el div con clase "product-card_name"
        title_tag = product.select_one("div.product-card_name")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"
        
        # Extraer precio final: se busca dentro del contenedor "mus-pro-price"
        price_container = product.select_one("div.mus-pro-price")
        if price_container:
            price_tag = price_container.find("span", {"data-test-item-price": True})
            if price_tag:
                price_value_tag = price_tag.find("span")
                final_price = price_value_tag.get_text(strip=True) if price_value_tag else "N/A"
                final_price = re.sub(r'[^\d,]', '', final_price)
            else:
                final_price = "N/A"
        else:
            final_price = "N/A"
        
        # Precio original (si se encuentra, ajustar selector según corresponda)
        original_price = "N/A"
        
        # Extraer link del producto: se busca el <a> con clase "mus-pro-thumb"
        a_tag = product.find("a", class_="mus-pro-thumb")
        if a_tag and "href" in a_tag.attrs:
            link = "https://www.musimundo.com" + a_tag["href"]
        else:
            link = "N/A"
        
        # Extraer imagen: se obtiene el src del <img>
        img_tag = product.find("img")
        image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
        
        # Determinar la categoría a partir de la URL (por ejemplo "climatizacion")
        url_parts = base_url.split("/")
        category = url_parts[3] if len(url_parts) > 3 else "N/A"
        
        # Inserción en la base de datos
        cursor.execute("""
            INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
        """, (title, original_price, final_price, link, image_url, category))
        
        print(f"Producto: {title} - Final: ${final_price}")
    except Exception as e:
        print("Error:", e)
        continue

# Cierre de Selenium y PostgreSQL
driver.quit()
conn.commit()
cursor.close()
conn.close()

print("Scrapeo completo.")
