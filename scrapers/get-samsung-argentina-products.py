from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import psycopg2
import os
from dotenv import load_dotenv

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

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Lista de URLs de categorías para Samsung Argentina
category_urls = [
    "https://www.samsung.com/ar/tvs/all-tvs/"
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

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    print(f"Scrapeando la categoría: {base_url}")
    driver.get(base_url)
    time.sleep(3)  # Esperar a que cargue la página inicial

    # Clic en el botón "Ver más" hasta que no esté disponible
    while True:
        try:
            ver_mas_btn = driver.find_element(By.CSS_SELECTOR, "button.pd19-product-finder__view-more-btn")
            if ver_mas_btn.is_displayed():
                print("Clic en 'Ver más' para cargar más productos...")
                driver.execute_script("arguments[0].click();", ver_mas_btn)
                time.sleep(3)  # Esperar a que se carguen nuevos productos
            else:
                break
        except Exception as e:
            print("No se encontró el botón 'Ver más' o ya no está disponible:", e)
            break

    # Obtener el HTML de la página con todos los productos cargados
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # Seleccionar todos los productos usando el contenedor de cada tarjeta
    products = soup.select("div.pd19-product-card__item")
    print(f"Se encontraron {len(products)} productos en la categoría.")

    for product in products:
        try:
            # Título: se extrae desde el <a> con la clase 'pd19-product-card__name'
            title_tag = product.find("a", class_="pd19-product-card__name")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # Link del producto: se obtiene el atributo href y se antepone el dominio
            if title_tag and "href" in title_tag.attrs:
                link = "https://www.samsung.com" + title_tag["href"]
            else:
                link = "N/A"

            # Precio final: se extrae el texto del <strong> con la clase 'pd19-product-card__current-price'
            price_tag = product.find("strong", class_="pd19-product-card__current-price")
            final_price = price_tag.get_text(strip=True).replace("$", "").replace(".", "") if price_tag else "N/A"

            # Precio original: en este caso no se detecta, se asigna N/A (se puede adaptar si se encuentra el elemento)
            original_price = "N/A"

            # Imagen: se toma la primera imagen encontrada en el contenedor de imagenes
            img_tag = product.select_one("a.pd19-product-card__img img.image__main")
            image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

            # Categoría: se extrae a partir de la URL base (se toma el último segmento; si la URL termina en '/', se toma el penúltimo)
            url_parts = base_url.rstrip("/").split("/")
            category = url_parts[-1] if url_parts[-1] != "" else url_parts[-2]

            # Inserción en la base de datos
            cursor.execute("""
                INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
            """, (title, original_price, final_price, link, image_url, category))

            print(f"Producto: {title} - Final: ${final_price} - Original: ${original_price}")
        except Exception as e:
            print("Error al procesar un producto:", e)
            continue

# Cierre de Selenium y PostgreSQL
driver.quit()
conn.commit()
cursor.close()
conn.close()

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print("\nScrapeo completo.")
print(f"Tiempo total de scrapeo: {elapsed_time:.2f} segundos.")
