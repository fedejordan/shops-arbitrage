from sqlalchemy import Column, Integer, Numeric, String, Float, DateTime, ForeignKey, func, Text
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
    retail_category = Column(String)  # Nota: la categoría se debe normalizar en el futuro
    added_date = Column(DateTime)
    updated_date = Column(DateTime)
    retailer = Column(String, index=True)  # opcional, si querés guardar redundancia textual
    retailer_id = Column(Integer, ForeignKey("retailers.id"))
    retailer = relationship("Retailer", back_populates="products")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category_rel = relationship("Category", backref="products")
    historical_prices = relationship("HistoricalPrice", back_populates="product")
    searchable_term = Column(Text)
    ai_description = Column(Text, nullable=True)


    @property
    def category_name(self):
        return self.category_rel.name if self.category_rel else None


class Retailer(Base):
    __tablename__ = "retailers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    products = relationship("Product", back_populates="retailer")

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

class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    original_price = Column(Numeric)
    final_price = Column(Numeric)
    date_recorded = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="historical_prices")
