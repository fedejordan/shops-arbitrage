from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configurar el navegador
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Ejecutar en modo sin interfaz (opcional)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL principal
driver.get("https://www.fravega.com/")

# Esperar a que cargue la página completamente
time.sleep(5)

# Expandir menú si es necesario (Frávega usa navegación lateral o superior)
# Buscamos enlaces del menú
category_links = set()

# Seleccionamos todos los enlaces visibles del header y navegación
all_links = driver.find_elements(By.TAG_NAME, "a")
for link in all_links:
    href = link.get_attribute("href")
    if href and "/l/" in href:
        category_links.add(href.split("?")[0])  # Limpiamos parámetros

# Mostramos los resultados
print("Categorías encontradas:")
for url in sorted(category_links):
    print(url)

# Cerrar navegador
driver.quit()
