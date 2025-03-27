from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv

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

all_products = []

# Medir tiempo de inicio
start_time = time.time()

# Scrapeo
for base_url in category_urls:
    for page in range(1, 25):  # Cambiá el rango si querés más o menos páginas por categoría
        print(f"Scrapeando {base_url} - Página {page}...")
        driver.get(f"{base_url}/?page={page}")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = soup.find_all("article", {"data-test-id": "result-item"})

        if not articles:
            print("No se encontraron productos en esta página.")
            break  # Si una página ya no tiene resultados, salir del bucle

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

                all_products.append({
                    "title": title,
                    "original_price": original_price.get_text(strip=True) if original_price else "",
                    "final_price": final_price.get_text(strip=True) if final_price else "",
                    "url": link,
                    "image": image_url,
                    "category": base_url.split("/l/")[-1]  # opcional: categoría para identificar el producto
                })

                print(f"Producto: {title} - ${final_price.get_text(strip=True)}")
            except Exception as e:
                print("Error:", e)

driver.quit()

# Guardar CSV
with open("fravega_productos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=all_products[0].keys())
    writer.writeheader()
    writer.writerows(all_products)

# Medir tiempo de fin
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\nScrapeo completo. {len(all_products)} productos guardados.")
print(f"Tiempo total de scrapeo: {elapsed_time:.2f} segundos.")