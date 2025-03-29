import requests

def search_mercadolibre(query, limit=10):
    url = "https://api.mercadolibre.com/sites/MLA/search"
    params = {
        "q": query,
        "limit": limit
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    results = response.json().get("results", [])
    products = []

    for item in results:
        products.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "sold_quantity": item.get("sold_quantity"),
            "permalink": item.get("permalink")
        })

    return products

def print_results(products):
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['title']}")
        print(f"   Precio: ${p['price']} - Vendidos: {p['sold_quantity']}")
        print(f"   Link: {p['permalink']}\n")

if __name__ == "__main__":
    query = input("🔍 Buscar en MercadoLibre: ")
    results = search_mercadolibre(query)
    print_results(results)
