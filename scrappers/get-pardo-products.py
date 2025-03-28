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

# Configuración de Selenium con tamaño de ventana forzado
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("window-size=1920,1080")
driver = webdriver.Chrome(options=options)

# Array de URLs de categorías
category_urls = [
    "https://www.pardo.com.ar/tv-y-video",
    "https://www.pardo.com.ar/rodados",
    "https://www.pardo.com.ar/bebes-y-ninos",
    "https://www.pardo.com.ar/equipaje",
    "https://www.pardo.com.ar/indumentaria-y-accesorios",
    "https://www.pardo.com.ar/audio",
    "https://www.pardo.com.ar/telefon%C3%ADa",
    "https://www.pardo.com.ar/informatica",
    "https://www.pardo.com.ar/electrodomesticos",
    "https://www.pardo.com.ar/climatizacion",
    "https://www.pardo.com.ar/hogar",
    "https://www.pardo.com.ar/jardin",
    "https://www.pardo.com.ar/belleza-y-salud"
    # Agrega más categorías si es necesario.
]

for category_url in category_urls:
    print(f"\nProcesando categoría: {category_url}")
    page = 1
    while True:
        print(f"Scrapeando {category_url} - Página {page}...")
        driver.get(f"{category_url}/?page={page}")
        time.sleep(3)  # Esperar a que se cargue la página

        # Parseamos el HTML con BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.vtex-search-result-3-x-galleryItem")

        # Si no se encuentran productos, se detiene la búsqueda en esa categoría
        if not products:
            print("No se encontraron productos en esta página. Finalizando búsqueda de esta categoría.")
            break

        # Recorremos cada producto encontrado
        for product in products:
            try:
                # Convertir el objeto Tag a string y volver a parsearlo (ya que no tiene get_attribute)
                soup_item = BeautifulSoup(str(product), "html.parser")
                section = soup_item.find("section", class_="vtex-product-summary-2-x-container")
                if not section:
                    continue

                title_tag = section.find("h3", class_="vtex-product-summary-2-x-productNameContainer")
                # Si no existe el h3, intentamos obtener el valor de aria-label
                title = title_tag.get_text(strip=True) if title_tag else section.get("aria-label", "").strip()

                a_tag = section.find("a", href=True)
                link = "https://www.pardo.com.ar" + a_tag["href"] if a_tag else ""

                img_tag = section.find("img")
                image_url = img_tag["src"] if img_tag and img_tag.get("src") else ""

                final_price_tag = section.find("span", class_="vtex-product-price-1-x-sellingPriceValue--summary")
                final_price = final_price_tag.get_text(strip=True) if final_price_tag else ""

                original_price_tag = section.find("span", class_="vtex-product-price-1-x-listPriceValue--summary")
                original_price = original_price_tag.get_text(strip=True) if original_price_tag else ""

                # Derivar la categoría quitando el dominio y las barras
                cat = category_url.replace("https://www.pardo.com.ar/", "").strip("/")

                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (title, original_price, final_price, link, image_url, cat))

                print(f"Producto: {title} - {final_price}")
            except Exception as e:
                print("Error al procesar un producto:", e)
                continue

        # Pasamos a la siguiente página
        page += 1

# Finalización
driver.quit()
conn.commit()
cursor.close()
conn.close()

print("\nScrapeo completo.")
