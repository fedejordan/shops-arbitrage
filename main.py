from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv

options = Options()
options.add_argument("--headless")  # corre sin abrir ventana
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

all_products = []

for page in range(1, 25):  # 24 páginas
    print(f"Scrapeando página {page}...")
    driver.get(f"https://www.fravega.com/l/tv-y-video/tv/?page={page}")
    time.sleep(3)  # importante: esperar a que cargue el JS

    soup = BeautifulSoup(driver.page_source, "html.parser")
    articles = soup.find_all("article", {"data-test-id": "result-item"})

    if not articles:
        print("No se encontraron productos en esta página.")
        continue

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
                "image": image_url
            })

            print(f"Producto: {title} - ${final_price.get_text(strip=True)}")
        except Exception as e:
            print("Error:", e)

driver.quit()

# Guardar CSV
with open("fravega_tvs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=all_products[0].keys())
    writer.writeheader()
    writer.writerows(all_products)

print(f"Scrapeo completo. {len(all_products)} productos guardados.")
