from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Configuración de Selenium con tamaño de ventana, user agent y opciones para evadir detección
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
driver = webdriver.Chrome(options=options)

# Array de URLs de categorías (sin barra final para formar correctamente la URL con ?page=)
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
]

def perform_advanced_scroll(max_attempts=5, wait_time=1):
    """
    Realiza un scroll avanzado que intenta cargar todos los productos mediante múltiples técnicas.
    """
    # 1. Scroll down poco a poco para simular comportamiento humano
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {total_height * i / 10});")
        time.sleep(0.3)
    
    # 2. Scroll hasta el final de la página
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(wait_time)
    
    # 3. Intenta encontrar el botón "Show more" o similar si existe
    try:
        more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Ver más') or contains(text(), 'Cargar más')]")
        if more_buttons:
            for button in more_buttons:
                driver.execute_script("arguments[0].click();", button)
                time.sleep(wait_time)
    except Exception as e:
        print(f"No se encontró botón de cargar más: {e}")
    
    # 4. Scroll up-down varias veces para forzar la carga de elementos
    for attempt in range(max_attempts):
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        # Scroll up a mitad de página
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(0.5)
        # Scroll down nuevamente
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        
        # Verificar si se han cargado más elementos después de cada intento
        products = driver.find_elements(By.CSS_SELECTOR, "div.vtex-search-result-3-x-galleryItem")
        print(f"Intento {attempt+1}: Se encontraron {len(products)} productos.")
        
        # Si ya tenemos 20 productos o más, podemos detenernos
        if len(products) >= 20:
            print(f"¡Éxito! Se encontraron {len(products)} productos.")
            break

def wait_for_products_to_load(min_products=20, timeout=30):
    """
    Espera explícitamente a que se cargue un mínimo de productos en la página.
    Retorna True si se cargan, False si no.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        products = driver.find_elements(By.CSS_SELECTOR, "div.vtex-search-result-3-x-galleryItem")
        print(f"Esperando... Encontrados {len(products)} productos.")
        if len(products) >= min_products:
            return True
        # Intenta scroll para ayudar a cargar
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    return False

for category_url in category_urls:
    print(f"\nProcesando categoría: {category_url}")
    page = 1
    while True:
        url_page = f"{category_url}/?page={page}"
        print(f"Scrapeando {url_page}...")
        
        # Cargar la página
        driver.get(url_page)
        time.sleep(3)  # Espera inicial para carga de la página
        
        # Esperar a que el contenedor de productos se cargue
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.vtex-search-result-3-x-galleryItem"))
            )
        except Exception as e:
            print(f"Error esperando el contenedor de productos: {e}")
            break
        
        # Realizar el scroll avanzado para cargar todos los productos
        perform_advanced_scroll()
        
        # Esperar explícitamente a que se carguen al menos 20 productos
        productos_cargados = wait_for_products_to_load(min_products=15, timeout=20)
        if not productos_cargados:
            print("No se pudieron cargar suficientes productos después de varios intentos.")
        
        # Guardamos el HTML para depuración
        # debug_filename = f"debug_{category_url.split('/')[-1]}_page{page}.html"
        # with open(debug_filename, "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        # print(f"HTML de debug guardado en: {debug_filename}")
        
        # Ahora usamos BeautifulSoup para extraer la información
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.vtex-search-result-3-x-galleryItem")
        print(f"BeautifulSoup encontró {len(products)} productos en la página {page}.")
        
        if not products:
            print("No se encontraron productos en esta página. Finalizando búsqueda de esta categoría.")
            break
            
        # Si encontramos menos de 8 productos, probablemente estamos en una página vacía o final
        if len(products) < 8:
            print(f"Solo se encontraron {len(products)} productos, posiblemente la última página. Finalizando categoría.")
            break
            
        for product in products:
            try:
                soup_item = BeautifulSoup(str(product), "html.parser")
                
                # Intenta diferentes patrones de selección para ser más robusto
                section = soup_item.find("section", class_="vtex-product-summary-2-x-container")
                if not section:
                    continue

                # Intentar obtener el título de diferentes maneras
                title_tag = section.find("h3", class_="vtex-product-summary-2-x-productNameContainer")
                title = title_tag.get_text(strip=True) if title_tag else section.get("aria-label", "").strip()
                
                if not title:
                    # Intentar otras clases para el título
                    alt_title_tag = section.find("span", class_="vtex-product-summary-2-x-productBrand")
                    title = alt_title_tag.get_text(strip=True) if alt_title_tag else ""

                # Obtener enlace del producto
                a_tag = section.find("a", href=True)
                link = "https://www.pardo.com.ar" + a_tag["href"] if a_tag else ""
                
                # Obtener imagen
                img_tag = section.find("img")
                image_url = img_tag["src"] if img_tag and img_tag.get("src") else ""
                
                # Intentar obtener precios de diferentes maneras
                final_price_tag = section.find("span", class_="vtex-product-price-1-x-sellingPriceValue--summary")
                final_price = final_price_tag.get_text(strip=True) if final_price_tag else ""
                
                if not final_price:
                    # Intentar con otras clases de precio
                    alt_price_tag = section.find(class_=lambda x: x and "sellingPrice" in x)
                    final_price = alt_price_tag.get_text(strip=True) if alt_price_tag else ""

                original_price_tag = section.find("span", class_="vtex-product-price-1-x-listPriceValue--summary")
                original_price = original_price_tag.get_text(strip=True) if original_price_tag else ""
                
                if not original_price:
                    alt_orig_tag = section.find(class_=lambda x: x and "listPrice" in x)
                    original_price = alt_orig_tag.get_text(strip=True) if alt_orig_tag else ""

                cat = category_url.replace("https://www.pardo.com.ar/", "").strip("/")
                
                # Si no tenemos título o enlace, saltamos este producto
                if not title or not link:
                    print("Producto sin título o enlace, saltando...")
                    continue

                # Insertar en la base de datos
                cursor.execute("""
                    INSERT INTO products (title, original_price, final_price, url, image, category, added_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO UPDATE SET 
                        title = EXCLUDED.title,
                        original_price = EXCLUDED.original_price,
                        final_price = EXCLUDED.final_price,
                        image = EXCLUDED.image,
                        updated_date = CURRENT_TIMESTAMP
                """, (title, original_price, final_price, link, image_url, cat))
                
                conn.commit()  # Confirmar después de cada producto para no perder datos

                print(f"Producto: {title} - {final_price}")
            except Exception as e:
                print(f"Error al procesar un producto: {e}")
                continue

        # Avanzar a la siguiente página
        page += 1
        
        # Opcionalmente, podemos limitar el número de páginas para pruebas
        # if page > 3:
        #     print("Límite de páginas alcanzado para esta categoría (prueba).")
        #     break

# Cerrar el driver y las conexiones
driver.quit()
cursor.close()
conn.close()

print("\nScrapeo completo.")