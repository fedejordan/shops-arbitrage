from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class RetailerBase(BaseModel):
    id: int
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
    ai_description: Optional[str] = None

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

class ProductListResponse(BaseModel):
    data: List[ProductBase]
    total: int
    page: int
    limit: int

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class SimpleOKResponse(BaseModel):
    ok: bool

class SimpleMessageResponse(BaseModel):
    message: str

class MapCategoryRequest(BaseModel):
    category_id: int

class SuggestedCategoryResponse(BaseModel):
    suggested_category_id: Optional[int]
    suggested_category_name: Optional[str] = None

class CountResponse(BaseModel):
    count: int

class PriceHistoryPoint(BaseModel):
    date: str  # ISO format string
    original_price: Optional[float]
    final_price: float

class AdminStats(BaseModel):
    total_products: int
    uncategorized_products: int
    products_with_history: int
    products_with_searchable_term: int
    total_retailers: int
    total_categories: int
    unmapped_retailer_categories: int
    products_with_ai_description: int
    invalid_price_products: int
    out_of_stock_products: int
    suspicious_discount_products: int