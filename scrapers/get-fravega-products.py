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
    "https://www.fravega.com/l/tv-y-video/tv",
    "https://www.fravega.com/l/lavado",
    "https://www.fravega.com/l/celulares",
    "https://www.fravega.com/l/heladeras-freezers-y-cavas",
    "https://www.fravega.com/l/hogar",
    "https://www.fravega.com/l/informatica",
    "https://www.fravega.com/l/cocina",
    "https://www.fravega.com/l/muebles",
    "https://www.fravega.com/l/pequenos-electrodomesticos",
    "https://www.fravega.com/l/audio",
    "https://www.fravega.com/l/deportes-y-fitness",
    "https://www.fravega.com/l/climatizacion",
    "https://www.fravega.com/l/videojuegos"
]

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    page = 1
    while True:
        print(f"Scrapeando {base_url} - Página {page}...")
        driver.get(f"{base_url}/?page={page}")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = soup.find_all("article", {"data-test-id": "result-item"})

        # Si no se encuentran productos, se sale del bucle para esta categoría.
        if not articles:
            print("No se encontraron productos en esta página. Finalizando la búsqueda de esta categoría.")
            break

        for article in articles:
            try:
                title = article.find("span", class_="sc-ca346929-0").get_text(strip=True)
                price_block = article.find("div", {"data-test-id": "product-price"})
                original_price = price_block.find("span", class_="sc-66d25270-0")
                final_price = price_block.find("span", class_="sc-1d9b1d9e-0")
                link_tag = article.find("a", href=True)
                link = "https://www.fravega.com" + link_tag["href"]
                img_tag = article.find("img")
                image_url = img_tag["src"] if img_tag else ""
                category = base_url.split("/l/")[-1]

                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET updated_date = CURRENT_TIMESTAMP
                """, (
                    title,
                    original_price.get_text(strip=True) if original_price else "",
                    final_price.get_text(strip=True) if final_price else "",
                    link,
                    image_url,
                    category
                ))

                print(f"Producto: {title} - ${final_price.get_text(strip=True) if final_price else 'N/A'}")
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
