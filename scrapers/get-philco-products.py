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

# Array de URLs de categorías de Philco
categories_urls = [
    "https://philco.com.ar/tecnologia-y-accesorios.html",
    "https://philco.com.ar/salud-y-belleza.html",
    "https://philco.com.ar/herramientas/ver-todo-herramientas.html",
    "https://philco.com.ar/electrodomesticos/aspiradoras.html",
    "https://philco.com.ar/electrodomesticos/termotanque.html",
    "https://philco.com.ar/electrodomesticos/cocina.html",
    "https://philco.com.ar/electrodomesticos/lavado.html",
    "https://philco.com.ar/electrodomesticos/heladeras-y-freezers.html",
    "https://philco.com.ar/movilidad/ver-todo-movilidad.html",
    "https://philco.com.ar/audio/audio.html",
    "https://philco.com.ar/tv/ver-todo-tv.html",
    "https://philco.com.ar/aire-climatizacion/ver-todo-aire-y-climatizacion.html"
]

# Medir tiempo de inicio
start_time = time.time()

# Iterar sobre cada categoría
for category_url in categories_urls:
    # Extraer la categoría de la URL (ejemplo: "tv", "aires", etc.)
    category = category_url.split("/")[3] if len(category_url.split("/")) > 3 else "N/A"
    
    print(f"\nScrapeando la categoría: {category_url} (Categoría: {category})...")
    driver.get(category_url)
    time.sleep(3)  # Espera a que cargue la página
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # Seleccionar todos los productos de la página
    products = soup.select("ol.products.list.items.product-items li.item.product.product-item")
    
    if not products:
        print("No se encontraron productos en la página.")
        continue

    for product in products:
        try:
            # Título: texto del enlace contenido en el h2
            title_tag = product.select_one("h2.product.name.product-item-name a.product-item-link")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # SKU: se encuentra en el párrafo con clase 'sku-producto'
            sku_tag = product.select_one("p.sku-producto")
            sku = sku_tag.get_text(strip=True) if sku_tag else "N/A"
            
            # Precio final: se busca dentro del span con clase 'special-price'
            final_price_tag = product.select_one("div.price-box.price-final_price span.special-price span.price")
            if final_price_tag:
                final_price = final_price_tag.get_text(strip=True)
                final_price = final_price.replace("$", "").replace("\xa0", "").replace(" ", "")
            else:
                final_price = "N/A"
            
            # Precio original: se busca en el span con clase 'old-price'
            original_price_tag = product.select_one("div.price-box.price-final_price span.old-price span.price")
            if original_price_tag:
                original_price = original_price_tag.get_text(strip=True)
                original_price = original_price.replace("$", "").replace("\xa0", "").replace(" ", "")
            else:
                original_price = "N/A"
            
            # Link del producto: href del enlace en el h2
            link_tag = product.select_one("h2.product.name.product-item-name a.product-item-link")
            link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "N/A"
            
            # Imagen: se toma el src del <img> con clase 'product-image-photo'
            img_tag = product.select_one("img.product-image-photo")
            image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
            
            # Inserción en la base de datos
            cursor.execute("""
                INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
            """, (title, original_price, final_price, link, image_url, category))
            
            print(f"Producto: {title} - Final: ${final_price} - Original: ${original_price} - Categoría: {category}")
        except Exception as e:
            print("Error:", e)
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
