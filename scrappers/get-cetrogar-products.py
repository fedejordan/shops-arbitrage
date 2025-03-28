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

# URL de la categoría en Cetrogar
category_urls = [
    "https://www.cetrogar.com.ar/tecnologia.html",
    "https://www.cetrogar.com.ar/electrodomesticos.html",
    "https://www.cetrogar.com.ar/bazar-y-decoracion.html",
    "https://www.cetrogar.com.ar/belleza-y-cuidado-personal.html",
    "https://www.cetrogar.com.ar/hogar.html",
    "https://www.cetrogar.com.ar/herramientas.html",
    "https://www.cetrogar.com.ar/deportes-y-fitness.html",
    "https://www.cetrogar.com.ar/bebes-y-ninos.html",
    "https://www.cetrogar.com.ar/otras-categorias.html"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        # La paginación se maneja con el query param "p"
        driver.get(f"{base_url}?p={page}")
        time.sleep(3)  # ajustar el tiempo de espera según sea necesario

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Buscar todos los productos usando el tag <li> con las clases correspondientes
        products = soup.find_all("li", class_="item product product-item images-deferred")
        
        # Si no se encuentran productos, se sale del bucle para esta categoría.
        if not products:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for product in products:
            try:
                # Extraer el título del producto
                title_tag = product.find("div", class_="product name product-item-name")
                title = title_tag.get_text(strip=True) if title_tag else "Sin título"

                # Extraer el link del producto (ya es una URL absoluta)
                link_tag = product.find("a", class_="product-item-info product-card", href=True)
                link = link_tag["href"] if link_tag else ""

                # Extraer la URL de la imagen
                img_tag = product.find("img", class_="product-image-photo")
                image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                # Extraer los precios
                price_box = product.find("div", class_="price-box price-final_price")
                original_price = ""
                final_price = ""
                if price_box:
                    # Se detecta descuento si existe el bloque "special-price"
                    discount_span = price_box.find("span", class_="special-price")
                    if discount_span:
                        # Producto con rebaja: se extrae el precio original y el precio especial
                        old_price_container = price_box.find("span", class_="old-price")
                        if old_price_container:
                            original_price_elem = old_price_container.find("span", class_="price")
                            original_price = original_price_elem.get_text(strip=True) if original_price_elem else ""
                        final_price_elem = discount_span.find("span", class_="price")
                        final_price = final_price_elem.get_text(strip=True) if final_price_elem else ""
                    else:
                        # Producto sin rebaja: se extrae el precio final directamente
                        final_price_elem = price_box.find("span", id=lambda x: x and x.startswith("product-price-"))
                        if not final_price_elem:
                            # Alternativa si no se encuentra por id: se buscan todos los spans con clase "price"
                            price_spans = price_box.find_all("span", class_="price")
                            if price_spans:
                                final_price = price_spans[-1].get_text(strip=True)
                        else:
                            final_price = final_price_elem.get_text(strip=True)

                # Definir la categoría a partir de la URL (se remueve el .html)
                category = base_url.split("/")[-1].replace(".html", "")

                # Insertar o actualizar en la base de datos
                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (
                    title,
                    original_price,
                    final_price,
                    link,
                    image_url,
                    category
                ))

                print(f"Producto: {title} - Final: {final_price} | Original: {original_price if original_price else 'N/A'}")
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
