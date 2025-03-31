from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    id: int
    title: str
    original_price: Optional[float]
    final_price: Optional[float]
    url: str
    image: str | None = None
    category: str
    added_date: datetime
    updated_date: datetime

    class Config:
        orm_mode = True
