from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    title: str
    original_price: Optional[float] = None
    final_price: float
    url: str
    image: Optional[str] = None
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    added_date: datetime
    updated_date: Optional[datetime] = None

    class Config:
        from_attributes = True  # Actualizado de orm_mode=True