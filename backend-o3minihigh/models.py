from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_price = Column(Float)
    final_price = Column(Float)
    url = Column(String)
    image = Column(String, nullable=True)
    category = Column(String)  # Nota: la categoría se debe normalizar en el futuro
    added_date = Column(DateTime)
    updated_date = Column(DateTime)
