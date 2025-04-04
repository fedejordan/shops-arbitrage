from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, RetailerCategory

def update_products_category_ids(db: Session):
    updated_count = 0

    # Tomamos todas las retailer_categories que ya tienen un category_id
    mappings = db.query(RetailerCategory).filter(RetailerCategory.category_id != None).all()

    for rc in mappings:
        # Para cada mapeo aplicamos la categoría al producto correspondiente
        products_to_update = db.query(Product).filter(
            Product.retailer_id == rc.retailer_id,
            Product.category == rc.name
        ).all()

        for product in products_to_update:
            product.category_id = rc.category_id
            updated_count += 1

        db.commit()

    print(f"✅ Se actualizaron {updated_count} productos con su category_id correspondiente.")

if __name__ == "__main__":
    db = SessionLocal()
    update_products_category_ids(db)
