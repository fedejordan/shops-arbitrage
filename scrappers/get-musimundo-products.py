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
options.add_argument("window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """
})

# Lista de URLs de categorías a scrapear
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

# Iterar sobre cada URL de la lista
for base_url in category_urls:
    print("Cargando página:", base_url)
    driver.get(base_url)
    time.sleep(5)  # Espera a que la página cargue
    print("Página cargada:", base_url)

    # Scroll dinámico hasta que no se carguen nuevos productos
    scroll_pause_time = 5
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_loops = 20  # Para evitar loops infinitos
    loops = 0

    while loops < max_loops:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        print(f"Scroll {loops+1} en {base_url}: altura actual = {new_height}")
        if new_height == last_height:
            break
        last_height = new_height
        loops += 1

    # Parsear el contenido cargado con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select("div.product-card")
    print(f"Productos cargados en {base_url}: {len(products)}")

    if not products:
        print("No se encontraron productos en", base_url)
        continue

    # Iterar sobre cada producto y extraer datos
    for product in products:
        try:
            # Extraer el título del producto
            title_tag = product.select_one("div.product-card_name")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            
            # Extraer el precio final
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
            
            # Precio original (ajusta el selector si la página lo muestra)
            original_price = "N/A"
            
            # Extraer el link del producto
            a_tag = product.find("a", class_="mus-pro-thumb")
            if a_tag and "href" in a_tag.attrs:
                link = "https://www.musimundo.com" + a_tag["href"]
            else:
                link = "N/A"
            
            # Extraer la URL de la imagen
            img_tag = product.find("img")
            image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
            
            # Determinar la categoría a partir de la URL (p.ej., "climatizacion")
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
