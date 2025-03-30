from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
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
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)

# URL de las categorías de Novogar
category_urls = [
    "https://www.novogar.com.ar/categorias/agua-caliente",
    "https://www.novogar.com.ar/categorias/aire-acondicionado",
    "https://www.novogar.com.ar/categorias/audio-y-video",
    "https://www.novogar.com.ar/categorias/bicicletas",
    "https://www.novogar.com.ar/categorias/calefaccion-",
    "https://www.novogar.com.ar/categorias/cocinas",
    "https://www.novogar.com.ar/categorias/colchones-y-sommier",
    "https://www.novogar.com.ar/categorias/cuidado-personal",
    "https://www.novogar.com.ar/categorias/electrodomesticos",
    "https://www.novogar.com.ar/categorias/fitness",
    "https://www.novogar.com.ar/categorias/gamer",
    "https://www.novogar.com.ar/categorias/heladeras",
    "https://www.novogar.com.ar/categorias/herramientas",
    "https://www.novogar.com.ar/categorias/informatica",
    "https://www.novogar.com.ar/categorias/jardin",
    "https://www.novogar.com.ar/categorias/lavado",
    "https://www.novogar.com.ar/categorias/limpieza-y-hogar",
    "https://www.novogar.com.ar/categorias/luces",
    "https://www.novogar.com.ar/categorias/muebles",
    "https://www.novogar.com.ar/categorias/seguridad-para-el-hogar",
    "https://www.novogar.com.ar/categorias/telefonia",
    "https://www.novogar.com.ar/categorias/television-",
    "https://www.novogar.com.ar/categorias/ventilacion"
]

# Medir tiempo de inicio
start_time = time.time()

# Función para hacer scroll hasta el final de la página y cargar todos los productos
def scroll_to_load_all_products(driver, max_scrolls=30):
    last_height = driver.execute_script("return document.body.scrollHeight")
    products_count = 0
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Obtener cantidad actual de productos
        soup = BeautifulSoup(driver.page_source, "html.parser")
        current_products = len(soup.select("div.one-product"))
        
        # Si encontramos nuevos productos, actualizar contador
        if current_products > products_count:
            products_count = current_products
            print(f"Productos encontrados hasta ahora: {products_count}")
        
        # Scroll hacia abajo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Esperar a que carguen los nuevos elementos
        
        # Calcular nueva altura
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Si la altura no cambia después de hacer scroll, hemos llegado al final
        if new_height == last_height:
            # Esperar un poco más para asegurarse de que no se cargan más productos
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Llegamos al final de la página")
                break
        
        last_height = new_height
        scroll_count += 1
    
    return products_count

# Scrapeo
for base_url in category_urls:
    print(f"\nScrapeando {base_url}...")
    
    try:
        # Cargar la página
        driver.get(base_url)
        time.sleep(3)  # Esperar carga inicial
        
        # Hacer scroll para cargar todos los productos
        total_products = scroll_to_load_all_products(driver)
        print(f"Total de productos encontrados en {base_url}: {total_products}")
        
        # Obtener HTML final con todos los productos cargados
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.one-product")
        
        # Si no se encuentran productos, pasar a la siguiente categoría
        if not products:
            print("No se encontraron productos en esta categoría.")
            continue
            
        # Obtener categoría de la URL
        category = base_url.split("/")[-1]
        
        # Procesar cada producto
        for product in products:
            try:
                # Título del producto
                title_tag = product.select_one("h3.product-card__name")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                
                # Link del producto
                a_tag = product.select_one("div.product-card a")
                link = "https://www.novogar.com.ar" + a_tag["href"] if a_tag and "href" in a_tag.attrs else "N/A"
                
                # Precio final (con descuento si existe)
                price_tag = product.select_one("p.frase_precio.cat-mobile-precioof")
                if price_tag:
                    final_price = price_tag.get_text(strip=True).replace("$", "").replace(".", "").strip()
                else:
                    # Buscar alternativa si no se encuentra el precio con clase cat-mobile-precioof
                    price_tag = product.select_one("div.productCard_prices p.productCard_price_regular:not(:has(~ p.productCard_price_discount))")
                    final_price = price_tag.get_text(strip=True).replace("$", "").replace(".", "").strip() if price_tag else "N/A"
                
                # Precio original (cuando hay descuento)
                original_price_tag = product.select_one("p.productCard_price_regular:has(~ p.productCard_price_discount)")
                if original_price_tag:
                    original_price = original_price_tag.get_text(strip=True).replace("$", "").replace(".", "").strip()
                else:
                    original_price = final_price  # Si no hay descuento, el precio original es igual al final
                
                # Imagen
                img_tag = product.select_one("div.productCard_img img")
                if img_tag and "src" in img_tag.attrs:
                    image_url = img_tag["src"]
                    # Añadir dominio si la URL es relativa
                    if image_url.startswith("/"):
                        image_url = "https://www.novogar.com.ar" + image_url
                else:
                    image_url = ""
                
                # Inserción en la base de datos
                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET 
                        title = EXCLUDED.title,
                        original_price = EXCLUDED.original_price,
                        final_price = EXCLUDED.final_price,
                        image = EXCLUDED.image,
                        updated_date = CURRENT_TIMESTAMP
                """, (title, original_price, final_price, link, image_url, category))
                
                print(f"Producto: {title} - Final: ${final_price} - Original: ${original_price}")
            
            except Exception as e:
                print(f"Error procesando producto: {e}")
                continue
    
    except Exception as e:
        print(f"Error scrapeando categoría {base_url}: {e}")
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