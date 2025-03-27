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

# URL de la categoría (puedes agregar más si lo requieres)
category_urls = [
    "https://www.naldo.com.ar/celulares/"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        # Se utiliza el query param "page"
        driver.get(f"{base_url}?page={page}")
        time.sleep(3)  # Esperar a que cargue la página
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Se busca el contenedor de cada producto usando el selector característico de Naldo
        products = soup.select("div.naldoar-search-result-3-x-galleryItem")
        
        # Si no se encuentran productos, se sale del bucle para esta categoría.
        if not products:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for product in products:
            try:
                # Título: se extrae del span con clase 'vtex-product-summary-2-x-productBrand'
                title_tag = product.find("span", class_="vtex-product-summary-2-x-productBrand")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                # Precio final: se extrae del span con clase 'vtex-product-price-1-x-sellingPriceValue'
                final_price_tag = product.select_one("span.vtex-product-price-1-x-sellingPriceValue")
                if final_price_tag:
                    final_price = final_price_tag.get_text(strip=True).replace("$", "").replace("\xa0", "")
                else:
                    final_price = "N/A"

                # Precio original: se extrae del span con clase 'vtex-product-price-1-x-listPriceValue'
                original_price_tag = product.select_one("span.vtex-product-price-1-x-listPriceValue")
                if original_price_tag:
                    original_price = original_price_tag.get_text(strip=True).replace("$", "").replace("\xa0", "")
                else:
                    original_price = "N/A"

                # Link del producto: se toma el href del <a> con clase 'vtex-product-summary-2-x-clearLink'
                a_tag = product.find("a", class_="vtex-product-summary-2-x-clearLink")
                link = "https://www.naldo.com.ar" + a_tag["href"] if a_tag and "href" in a_tag.attrs else "N/A"

                # Imagen: se toma el src del tag <img> con clase 'vtex-product-summary-2-x-image'
                img_tag = product.find("img", class_="vtex-product-summary-2-x-image")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                # Marca: en este caso no hay un selector explícito, se puede dejar vacío o parsear del título
                brand = ""

                # Categoría: derivada de la URL, asumiendo que es la carpeta intermedia
                # Ejemplo: "https://www.naldo.com.ar/celulares/" -> "celulares"
                parts = base_url.strip("/").split("/")
                category = parts[-1] if parts else "N/A"

                # Insertar en la base de datos
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
