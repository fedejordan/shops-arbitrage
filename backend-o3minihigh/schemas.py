from pydantic import BaseModel
from datetime import datetime

class ProductBase(BaseModel):
    id: int
    title: str
    original_price: float
    final_price: float
    url: str
    image: str | None = None
    category: str
    added_date: datetime
    updated_date: datetime

    class Config:
        orm_mode = True
