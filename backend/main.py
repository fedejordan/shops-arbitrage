from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Base, Category, RetailerCategory
import models
import schemas
from typing import List
from fastapi.middleware.cors import CORSMiddleware

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
@app.get("/products", response_model=List[schemas.ProductBase])
def read_products(query: str = "", db: Session = Depends(get_db)):
    print("Request a /products - query:", query)
    if query:
        products = db.query(models.Product).filter(models.Product.title.ilike(f"%{query}%")).all()
    else:
        products = db.query(models.Product).all()
    
    # Agregamos el nombre de la categoría manualmente
    # for product in products:
    #     if product.category_rel:
    #         product.category_name = product.category_rel.name  # esto funciona si lo seteaste como propiedad
    #     else:
    #         product.category_name = None

    return products

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