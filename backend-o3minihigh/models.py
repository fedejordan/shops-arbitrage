from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import relationship, foreign

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
    retailer = Column(String, index=True) 
    retailer_id = Column(Integer, ForeignKey("retailers.id"))  # 🔑 clave foránea
    retailer = relationship("Retailer")

class Retailer(Base):
    __tablename__ = "retailers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class RetailerCategory(Base):
    __tablename__ = 'retailer_categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    retailer_id = Column(Integer, ForeignKey('retailers.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)

    retailer = relationship("Retailer")
    category = relationship("Category")
