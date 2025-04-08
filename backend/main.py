from fastapi import FastAPI, Depends, HTTPException, Query
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

# Dependencia para obtener la sesión de la BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para obtener productos, con opción de búsqueda por título
@app.get("/products", response_model=schemas.ProductListResponse)
def read_products(
    query: str = "",
    sort: str = "",
    retailers: str = "",
    categories: str = "",
    minPrice: float = 0.0,
    maxPrice: float = 999999.0,
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

    # if categories:
    #     category_list = [c.strip() for c in categories.split(",")]
    #     q = q.join(models.Category, isouter=True).filter(models.Category.name.in_(category_list))

    # q = q.filter(models.Product.final_price >= minPrice, models.Product.final_price <= maxPrice)

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
