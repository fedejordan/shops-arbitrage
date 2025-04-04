from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RetailerBase(BaseModel):
    name: str

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    id: int
    title: str
    original_price: Optional[float]
    final_price: Optional[float]
    url: str
    image: str | None = None
    retail_category: str
    added_date: datetime
    updated_date: datetime
    retailer: RetailerBase
    category_id: Optional[int]
    category_name: Optional[str] = None

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    class Config:
        orm_mode = True

class RetailerCategoryBase(BaseModel):
    name: str
    retailer_id: int
    category_id: Optional[int]

class RetailerCategory(RetailerCategoryBase):
    id: int
    class Config:
        orm_mode = True
