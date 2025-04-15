from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Base, Category, RetailerCategory
import models
import schemas
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv
from sqlalchemy import func
import logging
from sqlalchemy.orm import joinedload
import time
from urllib.parse import unquote
from datetime import datetime, timedelta
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Configurar el logger para SQLAlchemy
logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Cargar las variables de entorno desde el archivo .env
app = FastAPI()

# Crear las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)

# Configurar CORS para desarrollo (ajusta en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Es recomendable especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para redirigir a HTTPS correctamente (opcional pero recomendable)
app.add_middleware(HTTPSRedirectMiddleware)

# Dependencia para obtener la sesión de la BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def fix_proto_header(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "https":
        scope = request.scope
        scope["scheme"] = "https"
    response = await call_next(request)
    return response


# Endpoint para obtener productos, con opción de búsqueda por título
@app.get("/products", response_model=schemas.ProductListResponse)
def read_products(
    query: str = "",
    sort: str = "",
    retailers: str = "",
    categories: str = "",
    minPrice: float = 0.0,
    maxPrice: float = 99999999.0,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    print(f"Request a /products - query: {query}, page: {page}, limit: {limit}")
    print("sort:", sort)    

    start_time = time.perf_counter()
    q = db.query(models.Product).options(
        joinedload(models.Product.retailer),
        joinedload(models.Product.category_rel)
    )

    if query:
        q = q.filter(models.Product.title.ilike(f"%{query}%"))

    if retailers:
        retailer_list = [r.strip() for r in retailers.split(",")]
        q = q.join(models.Retailer).filter(models.Retailer.name.in_(retailer_list))

    if categories:
        category_list = [c.strip() for c in categories.split("|")]
        q = q.join(models.Category, isouter=True).filter(models.Category.name.in_(category_list))

    q = q.filter(
        models.Product.final_price >= minPrice, 
        models.Product.final_price <= maxPrice,
        models.Product.out_of_stock == False
    )

    if sort == "price_asc":
        q = q.order_by(models.Product.final_price.asc())
    elif sort == "price_desc":
        q = q.order_by(models.Product.final_price.desc())
    elif sort == "name_asc":
        q = q.order_by(models.Product.title.asc())
    elif sort == "name_desc":
        q = q.order_by(models.Product.title.desc())
    elif sort == "retailer_asc":
        q = q.join(models.Retailer).order_by(models.Retailer.name.asc())
    elif sort == "retailer_desc":
        q = q.join(models.Retailer).order_by(models.Retailer.name.desc())
    elif sort == "date_asc":
        q = q.order_by(models.Product.added_date.asc())
    elif sort == "date_desc":
        q = q.order_by(models.Product.added_date.desc())
    else:
        q = q.order_by(models.Product.updated_date.desc(), models.Product.id.desc())

    total = q.count()

    products = q.offset(offset).limit(limit).all()

    duration = time.perf_counter() - start_time
    print(f"⏱️ Tiempo total de ejecución /products: {duration:.4f} segundos")

    return {
        "data": products,
        "total": total,
        "page": page,
        "limit": limit
    }


@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/categories/", response_model=list[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.post("/categories/", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/retailer-categories/unmapped", response_model=list[schemas.RetailerCategory])
def get_unmapped_retailer_categories(db: Session = Depends(get_db)):
    return db.query(RetailerCategory).filter(RetailerCategory.category_id == None).all()

@app.patch("/retailer-categories/{rc_id}/map")
def map_retailer_category(rc_id: int, category_id: int, db: Session = Depends(get_db)):
    rc = db.query(RetailerCategory).filter(RetailerCategory.id == rc_id).first()
    if not rc:
        raise HTTPException(status_code=404, detail="Retailer category not found")
    rc.category_id = category_id
    db.commit()
    return {"message": "Mapped successfully"}

@app.get("/products/uncategorized", response_model=List[schemas.ProductBase])
def get_uncategorized_products(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    return (
        db.query(models.Product)
        .filter(models.Product.category_id == None)
        .order_by(models.Product.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@app.get("/products/uncategorized/count")
def get_uncategorized_count(db: Session = Depends(get_db)):
    count = db.query(models.Product).filter(models.Product.category_id == None).count()
    return {"count": count}

@app.patch("/products/{product_id}/assign-category")
def assign_product_category(product_id: int, category_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.category_id = category_id
    db.commit()
    return {"message": "Category assigned successfully"}

@app.post("/products/{product_id}/suggest-category")
def suggest_category(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    categories = db.query(models.Category).all()
    category_names = [c.name for c in categories]

    prompt = (
        f"Dado el siguiente producto:\n\n"
        f"Título: {product.title}\n"
        f"Categorías disponibles: {', '.join(category_names)}\n\n"
        f"¿A cuál de estas categorías pertenece mejor este producto? Respondé solo con el nombre exacto de la categoría."
    )

    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

    try:
        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Sos un clasificador de productos."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            },
            timeout=15.0
        )
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    matched_category = next((c for c in categories if c.name.lower() == answer.lower()), None)

    if matched_category:
        return {"suggested_category_id": matched_category.id}
    else:
        return {"suggested_category_id": None, "suggested_category_name": answer}
    
@app.get("/retailers/", response_model=list[schemas.RetailerBase])
def get_retailers(db: Session = Depends(get_db)):
    return db.query(models.Retailer).order_by(models.Retailer.name.asc()).all()

from sqlalchemy import distinct

@app.get("/tweets/suggestions")
def get_tweet_suggestions(db: Session = Depends(get_db)):
    from collections import defaultdict
    import os
    import httpx
    import json
    import random
    import re

    # SELECT title AS match_key
    # FROM products
    # GROUP BY title
    # HAVING COUNT(DISTINCT retailer_id) > 1;
     # Subquery 1: títulos exactos repetidos entre retailers
    subquery_titles = (
        db.query(models.Product.title.label("match_key"))
        .group_by(models.Product.title)
        .having(func.count(distinct(models.Product.retailer_id)) > 1)
    )

    # select searchable_term, count(*) from products where searchable_term is not null group by searchable_term having count(distinct(retailer_id)) > 1
    # Subquery 2: searchable_terms repetidos entre retailers
    subquery_terms = (
        db.query(models.Product.searchable_term.label("match_key"))
        .filter(models.Product.searchable_term != None)
        .group_by(models.Product.searchable_term)
        .having(func.count(distinct(models.Product.retailer_id)) > 1)
    )

    # Unión de ambas subqueries (simulada en Python ya que SQLAlchemy no lo hace directo)
    union_keys = (
        subquery_titles.union(subquery_terms)
        .order_by(func.random())
        .limit(20)
        .subquery()
    )

     # Traer productos que coincidan por match_key
    productos = (
        db.query(models.Product)
        .filter(models.Product.out_of_stock == False)
        .join(union_keys, (models.Product.title == union_keys.c.match_key) | (models.Product.searchable_term == union_keys.c.match_key))
        .options(joinedload(models.Product.retailer))
        .order_by(models.Product.searchable_term.asc().nulls_last(), models.Product.title.asc(), models.Product.final_price.asc())
        .all()
    )

    # Agrupar por match_key (title o searchable_term)
    grouped = defaultdict(list)
    for p in productos:
        key = p.searchable_term or p.title
        grouped[key].append(p)

    casos = []
    for match_key, items in grouped.items():
        if len(items) < 2:
            continue
        sorted_items = sorted(items, key=lambda x: x.final_price)
        barato = sorted_items[0]
        caro = sorted_items[-1]
        diff = caro.final_price - barato.final_price
        if diff < 5000:
            continue

        casos.append({
            "case": len(casos)+1,
            "match_key": match_key,
            "title": barato.title,
            "retailer_barato": barato.retailer.name,
            "precio_barato": int(barato.final_price),
            "retailer_caro": caro.retailer.name,
            "precio_caro": int(caro.final_price),
            "diff": int(diff),
            "url": barato.url  # ✅ agregar la URL del más barato
        })

        if len(casos) >= 3:
            break

    if not casos:
        return []

    # Paso 2: crear prompt para DeepSeek
    prompt = (
        "Generá 3 tweets creativos por cada uno de los siguientes casos de arbitraje de productos. "
        "En cada tweet incluí una mención natural a nuestra plataforma 'TuPrecioIdeal' como fuente o herramienta que ayudó a encontrar la diferencia de precios. La cuenta de X es @TuPrecioIdealAr"
        "Incluí también el siguiente link del producto más barato al final del tweet para que la gente pueda verlo. Máximo 140 carácteres."
        "Respondé en formato JSON con el siguiente formato:\n\n"
        "[\n"
        "  {\n"
        "    \"case\": 1,\n"
        "    \"tweets\": [\"tweet1\", \"tweet2\", \"tweet3\"]\n"
        "  },\n"
        "  ...\n"
        "]\n\n"
    )

    for caso in casos:
        prompt += (
            f"Caso {caso['case']}:\n"
            f"Producto: {caso['title']}\n"
            f"Precio más barato: ${caso['precio_barato']} en {caso['retailer_barato']}\n"
            f"Precio más caro: ${caso['precio_caro']} en {caso['retailer_caro']}\n"
            f"Diferencia: ${caso['diff']}\n"
            f"Link: {caso['url']}\n\n"  # ✅ incluir el link en el prompt
        )

    print("Prompt para DeepSeek:", prompt)

    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

    try:
        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager experto en arbitraje de productos." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]

        print("Respuesta de DeepSeek:", raw)

        # Eliminar backticks si vienen
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    # Paso 3: combinar metadata del caso con tweets
    resultados = []
    for caso in casos:
        match = next((x for x in parsed if x["case"] == caso["case"]), None)
        if match and "tweets" in match:
            resultados.append({
                **caso,
                "tweets": match["tweets"]
            })

    return resultados


@app.get("/tweets/discounts")
def get_discount_tweets(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re

    # Buscar productos con al menos 25% de descuento (ajustable)
    productos = (
        db.query(models.Product)
        .join(models.Retailer)
        .filter(
            models.Product.original_price != None,
            models.Product.original_price > 0,
            models.Product.final_price < models.Product.original_price * 0.75,
            models.Product.out_of_stock == False
        )
        .order_by(func.random())
        .limit(5)
        .options(joinedload(models.Product.retailer))
        .all()
    )

    if not productos:
        return []

    prompt = (
        "Generá 2 tweets creativos por cada uno de los siguientes productos que tienen grandes descuentos. "
        "Incluí una mención a nuestra plataforma 'TuPrecioIdeal' en cada tweet, como si fuera la fuente que detectó la oferta. La cuenta de X es @TuPrecioIdealAr"
        "Usá estilo de redes sociales, emojis, y mostrá el precio original, precio final y porcentaje de descuento. "
        "Incluí el link al producto al final del tweet para que la gente pueda aprovecharlo. Máximo 140 carácteres."
        "Respondé en formato JSON con este formato:\n\n"
        "[\n"
        "  { \"title\": \"...\", \"tweets\": [\"...\", \"...\"] },\n"
        "  ...\n"
        "]\n\n"
    )

    productos_data = []
    for p in productos:
        descuento = round((1 - (p.final_price / p.original_price)) * 100)
        prompt += (
            f"Producto: {p.title}\n"
            f"Retailer: {p.retailer.name}\n"
            f"Precio original: ${int(p.original_price)}\n"
            f"Precio final: ${int(p.final_price)}\n"
            f"Descuento: {descuento}%\n"
            f"URL: {p.url}\n\n"  # ✅ Agregado
        )
        productos_data.append({
            "title": p.title,
            "retailer": p.retailer.name,
            "original_price": int(p.original_price),
            "final_price": int(p.final_price),
            "discount_pct": descuento,
            "url": p.url  # ✅ Agregado
        })

    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer " + deepseek_api_key,
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager experto en ofertas de productos." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]

        # limpiar markdown
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    # combinar datos de producto con los tweets
    resultados = []
    for pd in productos_data:
        match = next((x for x in parsed if x.get("title") and x["title"].lower() in pd["title"].lower()), None)
        if match and "tweets" in match:
            resultados.append({
                **pd,
                "tweets": match["tweets"]
            })

    return resultados


@app.get("/tweets/top-discounts")
def get_top_discount_tweets(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re

    productos = (
        db.query(models.Product)
        .join(models.Retailer)
        .filter(
            models.Product.original_price.isnot(None),
            models.Product.original_price > 0,
            models.Product.final_price < models.Product.original_price,
            models.Product.out_of_stock == False
        )
        .order_by((1 - models.Product.final_price / models.Product.original_price).desc())
        .limit(3)
        .options(joinedload(models.Product.retailer))
        .all()
    )

    if not productos:
        return []

    prompt = (
        "Generá 2 variantes de tweets creativos que comuniquen el top 3 de productos con mayores descuentos detectados hoy. "
        "Incluí los nombres de los productos, el porcentaje de descuento y mencioná a 'TuPrecioIdeal' como fuente. La cuenta de X es @TuPrecioIdealAr"
        "Usá emojis y lenguaje de redes sociales. "
        "Incluí también el link de cada producto para que los usuarios puedan acceder fácilmente. Máximo 140 carácteres."
        "Respondé en formato JSON así:\n\n"
        "[\"Tweet 1\", \"Tweet 2\"]\n\n"
        "Productos:\n"
    )

    for p in productos:
        pct = round(100 * (1 - float(p.final_price) / float(p.original_price)))
        prompt += f"- {p.title} -{pct}%\n  URL: {p.url}\n"

    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

    try:
        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager experto en ecommerce y descuentos." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    return parsed


@app.get("/tweets/historical-difference")
def get_biggest_historical_drop_tweet(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re
    from sqlalchemy import desc

    # Encontrar el producto con mayor diferencia absoluta histórica (original - final)
    best = (
        db.query(
            models.HistoricalPrice,
            models.Product.title,
            models.Product.url,
            models.Product.image,
            models.Retailer.name.label("retailer_name"),
            models.Product.original_price,
            models.Product.final_price
        )
        .join(models.Product, models.Product.id == models.HistoricalPrice.product_id)
        .join(models.Retailer, models.Retailer.id == models.Product.retailer_id)
        .filter(
            models.HistoricalPrice.original_price != None,
            models.HistoricalPrice.final_price != None,
            models.HistoricalPrice.original_price > models.HistoricalPrice.final_price,
            models.Product.out_of_stock == False
        )
        .order_by((models.HistoricalPrice.original_price - models.HistoricalPrice.final_price).desc())
        .limit(1)
        .first()
    )

    if not best:
        return []

    h, title, url, image, retailer, orig, final = best
    diff = round(h.original_price - h.final_price)
    pct = round(100 * (1 - h.final_price / h.original_price))

    prompt = (
        "Generá 3 tweets creativos sobre un producto con el mayor descuento histórico registrado en nuestra base de datos. "
        "Mencioná a 'TuPrecioIdeal' como la fuente que lo detectó. Incluí emojis, el precio original, precio actual y el porcentaje de ahorro. La cuenta de X es @TuPrecioIdealAr"
        "Agregá también el link del producto para que los usuarios puedan verlo. Máximo 140 carácteres."
        "Respondé en JSON con formato: {\"tweets\": [\"...\", \"...\", \"...\"]}\n\n"
        f"Producto: {title}\n"
        f"Retailer: {retailer}\n"
        f"Precio original: ${int(h.original_price)}\n"
        f"Precio más bajo registrado: ${int(h.final_price)}\n"
        f"Diferencia: ${diff}\n"
        f"Descuento: {pct}%\n"
        f"URL: {url}\n"  # ✅ Agregado
    )

    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager que crea contenido viral." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]

        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    return {
        "title": title,
        "retailer": retailer,
        "original_price": int(h.original_price),
        "final_price": int(h.final_price),
        "diff": diff,
        "discount_pct": pct,
        "url": url,  # ✅ Agregado a la respuesta por si lo querés mostrar también en frontend
        "tweets": parsed["tweets"]
    }


@app.get("/tweets/weekly-drops")
def get_weekly_drop_tweets(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    one_day_ago = datetime.utcnow() - timedelta(days=1)

    old_prices_subq = (
        db.query(
            models.HistoricalPrice.product_id,
            func.max(models.HistoricalPrice.date_recorded).label("old_date")
        )
        .filter(models.HistoricalPrice.date_recorded < three_days_ago)
        .group_by(models.HistoricalPrice.product_id)
        .subquery()
    )

    new_prices_subq = (
        db.query(
            models.HistoricalPrice.product_id,
            func.max(models.HistoricalPrice.date_recorded).label("new_date")
        )
        .filter(models.HistoricalPrice.date_recorded > one_day_ago)
        .group_by(models.HistoricalPrice.product_id)
        .subquery()
    )

    old_prices = (
        db.query(models.HistoricalPrice)
        .join(old_prices_subq, (models.HistoricalPrice.product_id == old_prices_subq.c.product_id) & (models.HistoricalPrice.date_recorded == old_prices_subq.c.old_date))
        .subquery()
    )

    new_prices = (
        db.query(models.HistoricalPrice)
        .join(new_prices_subq, (models.HistoricalPrice.product_id == new_prices_subq.c.product_id) & (models.HistoricalPrice.date_recorded == new_prices_subq.c.new_date))
        .subquery()
    )

    drops = (
        db.query(
            models.Product.title,
            models.Product.retailer_id,
            models.Product.url,  # ✅ Agregamos la URL
            old_prices.c.final_price.label("old_price"),
            new_prices.c.final_price.label("new_price"),
            (old_prices.c.final_price - new_prices.c.final_price).label("diff"),
            models.Retailer.name.label("retailer")
        )
        .join(old_prices, models.Product.id == old_prices.c.product_id)
        .join(new_prices, models.Product.id == new_prices.c.product_id)
        .join(models.Retailer, models.Retailer.id == models.Product.retailer_id)
        .filter(old_prices.c.final_price > new_prices.c.final_price)
        .filter(models.Product.out_of_stock == False)
        .order_by((old_prices.c.final_price - new_prices.c.final_price).desc())
        .limit(5)
        .all()
    )

    if not drops:
        return []

    prompt = (
        "Generá 2 tweets creativos por cada uno de los siguientes productos que bajaron de precio esta semana. "
        "Incluí el precio anterior, el nuevo, y cuánto bajó. Mencioná a 'TuPrecioIdeal' como la fuente. La cuenta de X es @TuPrecioIdealAr"
        "Usá emojis y lenguaje de redes. Agregá el link del producto al final de cada tweet. Máximo 140 carácteres. Respondé en JSON:\n\n"
        "[ { \"title\": \"...\", \"tweets\": [\"...\", \"...\"] }, ... ]\n\n"
    )

    result_data = []
    for d in drops:
        prompt += (
            f"Producto: {d.title}\n"
            f"Retailer: {d.retailer}\n"
            f"Precio antes: ${int(d.old_price)}\n"
            f"Precio ahora: ${int(d.new_price)}\n"
            f"Bajada: ${int(d.diff)}\n"
            f"URL: {d.url}\n\n"  # ✅ URL incluida en el prompt
        )
        result_data.append({
            "title": d.title,
            "retailer": d.retailer,
            "old_price": int(d.old_price),
            "new_price": int(d.new_price),
            "diff": int(d.diff),
            "url": d.url  # ✅ también la mantenemos en la respuesta
        })

    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager especializado en ecommerce." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )

        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error consultando DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al generar tweets con DeepSeek")

    resultados = []
    for item in result_data:
        match = next((x for x in parsed if x["title"].lower() in item["title"].lower()), None)
        if match:
            resultados.append({
                **item,
                "tweets": match["tweets"]
            })

    return resultados

@app.get("/tweets/educational")
def get_educational_tweets(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re

    prompt = (
        "Generá 2 tweets educativos sobre el concepto de arbitraje de precios entre retailers. "
        "El objetivo es que el usuario aprenda que si un producto está más barato en otro retailer, puede aprovechar la diferencia. "
        "Mencioná 'TuPrecioIdeal' como fuente que ayudó a detectar la diferencia. Usá tono claro, amigable, y si querés emojis. La cuenta de X es @TuPrecioIdealAr. Máximo 140 carácteres."
        "Respondé en formato JSON como una lista de tweets:\n\n"
        "[\"tweet 1\", \"tweet 2\"]\n\n"
    )

    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un educador financiero con enfoque en ecommerce." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        tweets = json.loads(raw)
        return tweets

    except Exception as e:
        print("❌ Error al consultar DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al generar tweets educativos")

@app.get("/tweets/polls")
def get_poll_tweet_ideas(db: Session = Depends(get_db)):
    import os
    import httpx
    import json
    import re

    # Obtener 4 productos con descuento (como opciones del poll)
    productos = (
        db.query(models.Product)
        .join(models.Retailer)
        .filter(
            models.Product.original_price != None,
            models.Product.original_price > 0,
            models.Product.final_price < models.Product.original_price,
            models.Product.out_of_stock == False
        )
        .order_by(func.random())
        .limit(4)
        .options(joinedload(models.Product.retailer))
        .all()
    )

    if len(productos) < 4:
        return []

    opciones = []
    prompt = (
        "Generá 2 variantes de tweets en formato encuesta (poll) con los siguientes productos, "
        "donde se invite al público a elegir cuál aprovecharían, mencionando los precios y la plataforma 'TuPrecioIdeal' como fuente. La cuenta de X es @TuPrecioIdealAr. Máximo 140 carácteres."
        "Respondé en JSON como lista de strings:\n\n"
        "[\"Tweet 1\", \"Tweet 2\"]\n\n"
        "Productos:\n"
    )

    for p in productos:
        pct = round((1 - p.final_price / p.original_price) * 100)
        prompt += f"- {p.title} ({p.retailer.name}): ${int(p.final_price)} (-{pct}%)\n"
        opciones.append(p.title)

    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    { "role": "system", "content": "Sos un community manager creativo especializado en ecommerce." },
                    { "role": "user", "content": prompt }
                ],
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]

        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)

    except Exception as e:
        print("❌ Error al generar encuesta con DeepSeek:", e)
        raise HTTPException(status_code=500, detail="Error al consultar DeepSeek")

    return parsed

@app.post("/tweets/post")
def post_tweet(payload: dict):
    import os
    from requests_oauthlib import OAuth1Session

    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Falta el texto del tweet")

    consumer_key = os.getenv("X_API_KEY")
    consumer_secret = os.getenv("X_API_KEY_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise HTTPException(status_code=500, detail="Faltan credenciales de X")

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text},
    )

    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Tweet publicado con éxito"}

from bs4 import BeautifulSoup

@app.get("/products/{product_id}", response_model=schemas.ProductBase)
def get_product_with_description(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .options(joinedload(models.Product.retailer), joinedload(models.Product.category_rel))
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if product.ai_description:
        return product

    # Intentar obtener HTML de la página del retailer
    page_content = ""
    try:
        response = httpx.get(product.url, timeout=10.0)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_content = soup.get_text(separator=" ", strip=True)
        page_content = page_content[:2000]  # límite de tokens para evitar textos muy largos
    except Exception as e:
        print("⚠️ Error obteniendo HTML del producto:", e)

    prompt = (
        f"Descripción de producto para ecommerce.\n\n"
        f"Título: {product.title}\n"
        f"Precio: ${int(product.final_price)}\n"
        f"Retailer: {product.retailer.name if product.retailer else 'Desconocido'}\n"
        f"Contenido de la página del producto:\n\n"
        f"{page_content}\n\n"
        f"Generá una descripción breve, clara, vendedora y sin repetir el título."
    )

    try:
        ds_response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Sos un copywriter experto en ecommerce."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=20.0
        )
        ds_response.raise_for_status()
        description = ds_response.json()["choices"][0]["message"]["content"].strip()
        product.ai_description = description
        db.commit()
    except Exception as e:
        print("❌ DeepSeek falló:", e)

    return product

@app.get("/products/{product_id}/history")
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(models.HistoricalPrice)
        .filter(models.HistoricalPrice.product_id == product_id)
        .order_by(models.HistoricalPrice.date_recorded.asc())
        .all()
    )

    if not history:
        return []

    return [
        {
            "date": h.date_recorded.isoformat(),
            "original_price": float(h.original_price) if h.original_price else None,
            "final_price": float(h.final_price)
        }
        for h in history
    ]

@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    return {
        "total_products": db.query(models.Product).count(),
        "uncategorized_products": db.query(models.Product).filter(models.Product.category_id == None).count(),
        "products_with_history": db.query(models.HistoricalPrice.product_id).distinct().count(),
        "products_with_searchable_term": db.query(models.Product).filter(models.Product.searchable_term != None).count(),
        "total_retailers": db.query(models.Retailer).count(),
        "total_categories": db.query(models.Category).count(),
        "unmapped_retailer_categories": db.query(models.RetailerCategory).filter(models.RetailerCategory.category_id == None).count(),
        "products_with_ai_description": db.query(models.Product).filter(models.Product.ai_description != None).count(),
        "invalid_price_products": db.query(models.Product)
            .filter(
                (models.Product.final_price == None) |
                (models.Product.final_price <= 0)
            ).count(),
        "out_of_stock_products": db.query(models.Product)
            .filter(models.Product.out_of_stock == True)
            .count()
    }

@app.get("/products/{product_id}/similar", response_model=List[schemas.ProductBase])
def get_similar_products(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .options(joinedload(models.Product.retailer))
        .filter(models.Product.id == product_id)
        .filter(models.Product.out_of_stock == False)
        .first()
    )
    if not product:
        return []

    similares = []

    # 1. Buscar por searchable_term
    if product.searchable_term:
        similares = (
            db.query(models.Product)
            .filter(
                models.Product.searchable_term == product.searchable_term,
                models.Product.id != product.id,
                models.Product.out_of_stock == False
            )
            .order_by(models.Product.final_price.asc())
            .limit(6)
            .all()
        )

    # 2. Si no hay suficientes, usar la categoría
    if len(similares) < 6 and product.category_id is not None:
        categoria_similares = (
            db.query(models.Product)
            .filter(
                models.Product.category_id == product.category_id,
                models.Product.id != product.id,
                models.Product.out_of_stock == False
            )
            .order_by(models.Product.final_price.asc())
            .limit(6 - len(similares))
            .all()
        )

        # Evitar duplicados
        ids_ya_incluidos = {p.id for p in similares}
        similares += [p for p in categoria_similares if p.id not in ids_ya_incluidos]

    return similares

