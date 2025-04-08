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
    filename='scraper_errors_garbarino.log',
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

# Configuración de Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Retailer info
retailer_name = "Garbarino"
retailer_url = "https://www.garbarino.com"

cursor.execute("""
    INSERT INTO retailers (name, url)
    VALUES (%s, %s)
    ON CONFLICT (url) DO NOTHING
""", (retailer_name, retailer_url))

cursor.execute("SELECT id FROM retailers WHERE url = %s", (retailer_url,))
retailer_id = cursor.fetchone()[0]

# Función para parsear precios
def parse_price(price_str):
    if not price_str or "N/A" in price_str:
        return None
    try:
        cleaned = re.sub(r"[^\d,]", "", price_str).replace(".", "").replace(",", ".")
        return float(cleaned)
    except Exception as e:
        logging.error(f"⚠️ Error al convertir precio: {price_str} - {e}")
        return None

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
    category = base_url.split("/")[-1]
    last_product_urls = set()
    while True:
        print(f"Scrapeando {category} - Página {page}...")
        current_product_urls = set()
        try:
            driver.get(f"{base_url}?page={page}")
            time.sleep(3)  # Esperar a que cargue la página

            # Verificar si estamos en una página de resultados o una página de categoría
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Buscar productos con la nueva clase
            # products = soup.find_all("div", class_=lambda x: x and "product-card-design8-vertical-wrapper" in x)
            # En lugar de buscar una clase específica
            products = soup.find_all("div", class_=lambda cls: cls and "product-card" in cls and "vertical-wrapper" in cls)
            
            if not products:
                print(f"🚫 No se encontraron productos en {category} página {page}. Fin de categoría.")
                break

            for product in products:
                try:
                    # Buscar el título del producto con la nueva clase
                    # title_tag = product.find("div", class_=lambda x: x and "product-card-design8-vertical__name" in x)
                    title_tag = product.find("div", class_=lambda cls: cls and "product-card" in cls and "__name" in cls)
                    title = title_tag.get_text(strip=True) if title_tag else "Sin título"
                    
                    # Buscar marca del producto (nuevo)
                    # brand_tag = product.find("div", class_=lambda x: x and "product-card-design8-vertical__brand" in x)
                    brand_tag = product.find("div", class_=lambda x: x and "product-card" in x and "__brand" in x)
                    brand = brand_tag.get_text(strip=True) if brand_tag else ""
                    
                    # Si hay marca, agregarla al título si no está ya incluida
                    # if brand and brand.lower() not in title.lower():
                    #     title = f"{brand} - {title}"

                    # Buscar el precio actual con la nueva clase
                    # final_price_container = product.find("div", class_=lambda x: x and "product-card-design8-vertical__price" in x)
                    final_price_container = product.find("div", class_=lambda cls: cls and "product-card" in cls and "__price" in cls)
                    final_price_str = ""
                    if final_price_container:
                        spans = final_price_container.find_all("span")
                        # Extraer todos los textos y concatenarlos
                        final_price_str = "".join([span.get_text(strip=True) for span in spans])
                    
                    # Buscar el precio original (si existe)
                    # original_price_container = product.find("div", class_="product-card-design8-vertical__prev-price", recursive=True)
                    original_price_container = product.find("div", class_=lambda cls: cls and "product-card" in cls and "__prev-price" in cls)
                    original_price_str = ""
                    if original_price_container:
                        spans = original_price_container.find_all("span")
                        original_price_str = "".join([span.get_text(strip=True) for span in spans])
                    
                    # Buscar el enlace del producto
                    link_tag = product.find("a", class_=lambda x: x and "card-anchor" in x)
                    link = retailer_url + link_tag["href"] if link_tag and "href" in link_tag.attrs else ""
                    current_product_urls.add(link)

                    # Buscar la imagen del producto
                    img_tag = product.find("img", class_="ratio-image__image")
                    image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                    
                    # En caso de no encontrar la clase de imagen, buscar cualquier imagen
                    # if not image_url:
                    #     img_tag = product.find("img")
                    #     image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                    # Parsear precios
                    original_price = parse_price(original_price_str)
                    final_price = parse_price(final_price_str)
                    
                    # Si no hay precio original, pero hay precio final, asignar el mismo precio
                    # if not original_price and final_price:
                    #     original_price = final_price

                    print(f"Producto: {title} | URL: {link} | Precio Final: {final_price_str} | Precio Original: {original_price_str}")

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

                    # Insertar en la base de datos solo si tenemos un titulo y una URL
                    if title != "Sin título" and link:
                        cursor.execute("""
                            INSERT INTO products (title, original_price, final_price, url, image, retail_category, retailer_id, added_date, updated_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (url) DO UPDATE SET 
                                title = EXCLUDED.title,
                                original_price = EXCLUDED.original_price,
                                final_price = EXCLUDED.final_price,
                                image = EXCLUDED.image,
                                category = EXCLUDED.category,
                                retailer_id = EXCLUDED.retailer_id,
                                updated_date = CURRENT_TIMESTAMP
                        """, (
                            title,
                            original_price,
                            final_price,
                            link,
                            image_url,
                            category,
                            retailer_id
                        ))

                        print(f"✔ Producto: {title} | Final: {final_price} | Original: {original_price if original_price else 'N/A'}")

                except Exception as e:
                    logging.error(f"🛑 Error procesando producto en {category} página {page}: {e}")
                    continue

            # 🛑 DETECCIÓN DE LOOP INFINITO
            if current_product_urls == last_product_urls:
                print(f"🌀 Página {page} de {category} repite los mismos productos. Finalizando categoría.\n")
                break

            conn.commit()
            print(f"💾 Página {page} de {category} guardada.\n")
            page += 1

            last_product_urls = current_product_urls

        except Exception as e:
            logging.error(f"🔥 Error al cargar página {page} de {category}: {e}")
            break

# Cierre de Selenium y PostgreSQL
driver.quit()
cursor.close()
conn.close()

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\n✅ Scrapeo completo.")
print(f"⏱ Tiempo total: {elapsed_time:.2f} segundos.")