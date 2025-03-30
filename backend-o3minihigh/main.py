from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
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
    return products
