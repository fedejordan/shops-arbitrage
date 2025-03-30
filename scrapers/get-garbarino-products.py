from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# URLs de las categorías
category_urls = [
    "https://www.garbarino.com/celulares-notebooks-y-tecnologia",
    "https://www.garbarino.com/smart-tv-audio-y-video",
    "https://www.garbarino.com/electrodomesticos",
    "https://www.garbarino.com/salud-y-belleza",
    "https://www.garbarino.com/hogar-muebles-y-jardin",
    "https://www.garbarino.com/bebes-y-ninos",
    "https://www.garbarino.com/deportes-y-tiempo-libre",
    "https://www.garbarino.com/construccion",
    "https://www.garbarino.com/herramientas",
    "https://www.garbarino.com/animales-y-mascotas",
    "https://www.garbarino.com/moda-y-accesorios",
    "https://www.garbarino.com/arte-libreria-y-merceria",
    "https://www.garbarino.com/mas-categorias"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        driver.get(f"{base_url}?page={page}")
        time.sleep(3)  # Esperar a que cargue la página

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Se busca el contenedor de cada producto
        products = soup.find_all("div", class_="product-card-design6-vertical-wrapper")

        # Si no se encuentran productos, se sale del bucle para esta categoría.
        if not products:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for product in products:
            try:
                # Título
                title_tag = product.find("div", class_="product-card-design6-vertical__name")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                
                # Precio final: se busca el contenedor exacto con la clase correspondiente
                final_price_container = product.select_one("div.product-card-design6-vertical__price")
                if final_price_container:
                    spans = final_price_container.find_all("span")
                    final_price = spans[-1].get_text(strip=True).replace("$", "") if spans else "N/A"
                else:
                    final_price = "N/A"

                # Precio original: se busca el contenedor exacto con la clase para precio anterior
                original_price_container = product.select_one("div.product-card-design6-vertical__prev-price")
                if original_price_container:
                    # Buscamos el div que contiene los spans del precio anterior
                    orig_price_div = original_price_container.select_one("div.text-no-wrap.grey--text")
                    if orig_price_div:
                        orig_spans = orig_price_div.find_all("span")
                        original_price = orig_spans[-1].get_text(strip=True).replace("$", "") if orig_spans else "N/A"
                    else:
                        original_price = "N/A"
                else:
                    original_price = "N/A"

                
                # Link del producto
                a_tag = product.find("a", class_="card-anchor")
                link = "https://www.garbarino.com" + a_tag["href"] if a_tag and "href" in a_tag.attrs else "N/A"
                
                # Imagen (se toma la primera imagen encontrada)
                img_tag = product.find("img", class_="ratio-image__image")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                
                # Marca
                brand_tag = product.find("div", class_="product-card-design6-vertical__brand")
                brand = brand_tag.get_text(strip=True) if brand_tag else ""
                
                # Categoría (derivada de la URL)
                category = base_url.split("/")[-1]

                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (title, original_price, final_price, link, image_url, category))
                
                print(f"Producto: {title} - Final: ${final_price} - Original: ${original_price}")
            except Exception as e:
                print("Error:", e)
                continue

        page += 1  # Pasar a la siguiente página


# Cierre de Selenium y PostgreSQL
driver.quit()
conn.commit()
cursor.close()
conn.close()

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\nScrapeo completo.")
print(f"Tiempo total de scrapeo: {elapsed_time:.2f} segundos.")
