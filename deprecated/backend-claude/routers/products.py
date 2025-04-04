from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search", response_model=List[schemas.Product])
def search_products(
    q: str = Query(..., min_length=1, description="Texto a buscar"),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Buscar productos por título, categoría y/o rango de precios
    """
    query = db.query(models.Product)
    
    # Búsqueda por texto (título)
    if q:
        query = query.filter(models.Product.title.ilike(f"%{q}%"))
    
    # Filtro por categoría
    if category:
        query = query.filter(models.Product.category.ilike(f"%{category}%"))
    
    # Filtro por precio mínimo
    if min_price is not None:
        query = query.filter(models.Product.final_price >= min_price)
    
    # Filtro por precio máximo
    if max_price is not None:
        query = query.filter(models.Product.final_price <= max_price)
    
    # Ordenar por precio ascendente
    products = query.order_by(models.Product.final_price).all()
    
    return products

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Obtener un producto por su ID
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product