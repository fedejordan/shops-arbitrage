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

# URLs de las categorías de Megatone
category_urls = [
    "https://www.megatone.net/listado/tv-audio-video/",
    "https://www.megatone.net/listado/tecnologia/",
    "https://www.megatone.net/listado/electrodomesticos/",
    "https://www.megatone.net/listado/pequenos-electro-salud/",
    "https://www.megatone.net/listado/hogar-deco/",
    "https://www.megatone.net/listado/hogar-jardin/",
    "https://www.megatone.net/listado/jardin-herramientas-construccion/",
    "https://www.megatone.net/listado/deportes-tiempo-libre/",
    "https://www.megatone.net/listado/bebes-ninos/",
    "https://www.megatone.net/listado/otras-categorias/"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        # Usamos el parámetro de paginado ?p_=
        url = f"{base_url}?p_={page}"
        driver.get(url)
        time.sleep(3)  # Espera para que cargue la página

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Se buscan los contenedores de productos mediante el <a> con la clase "CajaProductoGrillaListado"
        products = soup.find_all("a", class_="CajaProductoGrillaListado")

        # Si no se encuentran productos, se finaliza el scrapeo de la categoría.
        if not products:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for product in products:
            try:
                # Título: se extrae del <h3> con la clase "TituloListado"
                title_tag = product.find("h3", class_="TituloListado")
                title = title_tag.get_text(strip=True) if title_tag else "Sin Título"

                # Precios:
                # Primero se busca el contenedor del precio original (PrecioTachado)
                original_price_tag = product.select_one("div.PrecioTachado")
                original_price_text = original_price_tag.get_text(strip=True) if original_price_tag else ""
                
                if original_price_text:
                    # Producto en rebaja: se extrae el precio final del contenedor con la clase "Precio fNova-Light"
                    final_price_tag = product.select_one("div.Precio.fNova-Light")
                    final_price_text = final_price_tag.get_text(strip=True) if final_price_tag else ""
                else:
                    # Producto sin rebaja: se toma el precio final del contenedor "Precio AjustePrecioMostrado"
                    final_price_tag = product.select_one("div.Precio.AjustePrecioMostrado")
                    final_price_text = final_price_tag.get_text(strip=True) if final_price_tag else ""
                    original_price_text = ""  # Se mantiene vacío
                    
                # URL: se extrae del atributo href del <a>, se completa si es relativa
                link = product.get("href")
                if link and not link.startswith("http"):
                    link = "https://www.megatone.net" + link

                # Imagen: se obtiene del <img> con la clase "imagenListado"
                img_tag = product.find("img", class_="imagenListado")
                image_url = img_tag.get("src") if img_tag else ""

                # Categoría: se extrae de la URL base (último segmento de la ruta)
                category = base_url.strip("/").split("/")[-1]

                # Inserción en la base de datos
                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (
                    title,
                    original_price_text,
                    final_price_text,
                    link,
                    image_url,
                    category
                ))

                print(f"Producto: {title} - {final_price_text}")
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
