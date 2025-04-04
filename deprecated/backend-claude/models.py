from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    # Cambiamos a Text para manejar títulos más largos
    title = Column(Text, index=True)
    original_price = Column(Float, nullable=True)
    final_price = Column(Float)
    # Cambiamos a Text para URLs más largas
    url = Column(Text)
    image = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    added_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())