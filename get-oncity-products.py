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

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# URL de la categoría de On City
category_urls = [
    "https://www.oncity.com/aire-libre",
    "https://www.oncity.com/audio-tv-y-video",
    "https://www.oncity.com/arte-libreria-y-merceria",
    "https://www.oncity.com/bebes",
    "https://www.oncity.com/belleza-y-cuidado-personal",
    "https://www.oncity.com/compra-internacional",
    "https://www.oncity.com/deportes-y-fitness",
    "https://www.oncity.com/electrodomesticos",
    "https://www.oncity.com/herramientas-y-construccion",
    "https://www.oncity.com/hogar",
    "https://www.oncity.com/iluminacion",
    "https://www.oncity.com/juegos-y-juguetes",
    "https://www.oncity.com/mascotas",
    "https://www.oncity.com/muebles",
    "https://www.oncity.com/salud-y-equipamiento-medico",
    "https://www.oncity.com/tecnologia",
    "https://www.oncity.com/tiempo-libre",
    "https://www.oncity.com/Autos-y-Motos",
    
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while page == 1:
        print(f"Scrapeando {base_url} - Página {page}...")
        driver.get(f"{base_url}?page={page}")
        time.sleep(3)  # Esperar a que cargue la página
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Se busca el contenedor de cada producto usando el selector de On City
        products = soup.select("div.vtex-search-result-3-x-galleryItem")
        
        # Si no se encuentran productos, finaliza el bucle para esta categoría
        if not products:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for product in products:
            try:
                # Título: se toma el texto del span que contiene el nombre del producto
                title_tag = product.find("span", class_="vtex-product-summary-2-x-productBrand")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                
                # Precio final: se busca el contenedor del precio de venta
                final_price_container = product.find("span", class_="vtex-product-price-1-x-sellingPrice")
                if final_price_container:
                    # Se limpia el texto para obtener solo el precio (ejemplo: "299.999")
                    final_price = final_price_container.get_text(strip=True).replace("$", "").replace("\xa0", "").replace(" ", "")
                else:
                    final_price = "N/A"
                    
                # Precio original: se busca el contenedor del precio anterior (si existe)
                original_price_container = product.find("span", class_="vtex-product-price-1-x-listPrice")
                if original_price_container:
                    original_price = original_price_container.get_text(strip=True).replace("$", "").replace("\xa0", "").replace(" ", "")
                else:
                    original_price = "N/A"

                # Link del producto: se obtiene a partir del <a> con la clase correspondiente
                a_tag = product.find("a", class_="vtex-product-summary-2-x-clearLink")
                link = "https://www.oncity.com" + a_tag["href"] if a_tag and "href" in a_tag.attrs else "N/A"
                
                # Imagen: se toma la primera imagen encontrada con la clase de la imagen principal
                img_tag = product.find("img", class_="vtex-product-summary-2-x-imageNormal")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                
                # Categoría (derivada de la URL)
                category = base_url.split("/")[-1]
                
                # Inserción en la base de datos
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

print("\nScrapeo completo.")
print(f"Tiempo total de scrapeo: {elapsed_time:.2f} segundos.")
