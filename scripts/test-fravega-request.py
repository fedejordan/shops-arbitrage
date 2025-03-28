import requests
from bs4 import BeautifulSoup

url = "https://www.fravega.com/l/tv-y-video/tv/?page=1"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
print("Contenido:", response.text[:1000])  # mostramos solo un fragmento

soup = BeautifulSoup(response.text, "html.parser")
articles = soup.find_all("article", {"data-test-id": "result-item"})
print("Productos encontrados:", len(articles))
